import shutil
from pathlib import Path
import concurrent.futures
from datetime import datetime
from collections import defaultdict
from typing import List, Union, Dict, Optional

from tqdm import tqdm
import reverse_geocoder as rg

from media_organizer.utils import handle_single_or_list
from media_organizer.timeshift import (
    extract_metadata_using_exiftool,
    get_capture_datetime,
    GPSCoordinates,
    get_timezone,
)


@handle_single_or_list(is_file_path=True)
def _get_rename_plan(
    file_paths: Union[Path, str, List[Union[Path, str]]],
    return_suffixless: bool = False,
) -> Dict[Path, Path]:
    """Return a dictionary of file paths to their new file paths.
    The new file paths are generated using the following format:
    <date>-<city>-<device>.<extension>
    <date> is the capture datetime of the file in ISO 8601 format.
    <city> is the city where the file was captured (if GPS info is available).
    <device> is the device used to capture the file.
    <extension> is the file extension.
    """
    # Part 1: capture datetime.
    print("Extracting capture datetimes...")
    metadatas = extract_metadata_using_exiftool(file_paths)
    capture_datetimes = get_capture_datetime(
        file_paths, metadatas=metadatas, force_return_timezone=True
    )
    if not isinstance(capture_datetimes, list):
        capture_datetimes = [capture_datetimes]

    # Part 2: city name
    print("Extracting city names...")
    gps_coords = GPSCoordinates.from_exif_metadata(metadatas)
    city_names = gps_coords_to_city_name(gps_coords)
    if not isinstance(city_names, list):
        city_names = [city_names]

    # Part 3: device name
    print("Extracting device names...")
    device_names = extract_device_name_from_metadata(metadatas)
    if not isinstance(device_names, list):
        device_names = [device_names]

    # Now putting it all together.
    print("Generating rename plan...")
    new_names = {}
    iterator = zip(file_paths, capture_datetimes, city_names, device_names)
    for file_path, *info_triplet in iterator:
        info_triplet = [part for part in info_triplet if part is not None]
        if len(info_triplet) == 0:
            # This happens with empty files for instance. In which case,
            # we don't consider this file in the rename plan.
            continue

        # The first element should always be there: it's the capture datetime.
        info_triplet[0] = format_capture_datetime_for_file_renaming(info_triplet[0])

        # Applying with_suffix("") to remove the extension and make the function
        # more 'general'. This way the rename plan can be used for other filetypes
        # like XMP, RAF, etc.
        new_name = Path("-".join(info_triplet))
        suffix = "" if return_suffixless else file_path.suffix
        new_name = new_name.with_suffix(suffix)
        key = file_path if not return_suffixless else file_path.with_suffix("")
        new_names[key] = new_name

    # Handle duplicates. This corresponds to the case where two files have the same capture datetime.
    # (for instance: burst mode on a camera).
    # TODO: put this in a dedicated function. Change the variable names to make
    # it more readable/readable.
    print("Handling duplicates...")
    reverse_file_dict = defaultdict(list)
    for original_name, new_name in new_names.items():
        reverse_file_dict[new_name].append(original_name)

    for new_name, original_names in reverse_file_dict.items():
        if len(original_names) > 1:
            original_names = sorted(original_names)
            for count, original_name in enumerate(
                original_names[1:], 1
            ):  # start with 1 for suffix and skip the first file
                stem = new_name.stem
                new_names[original_name] = new_name.with_stem(f"{stem}-{count}")

    return new_names


def format_capture_datetime_for_file_renaming(dt: datetime) -> str:
    """Return a capture datetime formatted for file renaming."""
    date_part = dt.strftime("%Y-%m-%d")
    time_part = dt.strftime("%H-%M-%S")
    tz_part = dt.strftime("%z").replace("+", "p").replace("-", "m")
    return f"{date_part}_{time_part}_{tz_part}"


@handle_single_or_list()
def gps_coords_to_city_name(gps_coords: List[GPSCoordinates]) -> List[Union[str, None]]:
    """Get the city name from the GPS coordinates."""
    # reverse_geocoding is expecting all non-None GPSCoordinates.
    # But gps_coords is a list that might contain None values.
    # We need to pre-filter and keep track of the original indexes.

    non_null_indices = [i for i, x in enumerate(gps_coords) if x is not None]
    non_null_gps_coords = [x.to_tuple() for x in gps_coords if x is not None]
    if len(non_null_gps_coords) == 0:
        return [None] * len(gps_coords)

    city_names = [None] * len(gps_coords)
    hits = rg.search(non_null_gps_coords)
    for index, hit in zip(non_null_indices, hits):
        city_names[index] = hit["name"]

    return city_names


@handle_single_or_list(is_embarrassingly_parallel=True)
def extract_device_name_from_metadata(metadata: Dict[str, str]) -> str:
    """Extract the device name from the metadata of a file."""
    parts = []
    if "EXIF:Make" in metadata:
        parts.append(metadata["EXIF:Make"].capitalize())
    if "EXIF:Model" in metadata:
        parts.append(metadata["EXIF:Model"])
    if any(["gopro" in key.lower() for key in metadata.keys()]):
        parts.append("GoPro")

    if len(parts) == 0:
        return None
    return "_".join(parts)


def rename(
    file_paths: Union[Path, str, List[Union[Path, str]]],
    output_dir: Path = None,
    create_backups: bool = True,
    _rename_plan: Dict[Path, Path] = None,
) -> Dict[Path, Path]:
    """Return a dictionary of file paths to their new file paths.
    The new file paths are generated using the following format:
    <date>-<city>-<device>.<extension>
    <date> is the capture datetime of the file in ISO 8601 format.
    <city> is the city where the file was captured (if GPS info is available).
    <device> is the device used to capture the file.
    <extension> is the file extension.

    Args:
        file_paths: The file paths to rename.
        output_dir: The directory to move the renamed files to.
                    If None, the files will be moved to the same directory as the original files.
        create_backups: Whether to create a backup of the original file.
    """
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

    rename_plan = (
        _rename_plan if _rename_plan is not None else _get_rename_plan(file_paths)
    )

    # TODO: SO f*cking ugly.
    # The "handle_single_or_list" decorator was a bad idea.
    if isinstance(rename_plan, dict):
        input_paths = list(rename_plan.keys())
        output_paths = list(rename_plan.values())
    elif isinstance(rename_plan, str) and isinstance(file_paths, list):
        input_paths = file_paths
        output_paths = [rename_plan]
    else:
        input_paths = [file_paths]
        output_paths = [rename_plan]

    if output_dir is None:
        # If no output directory is specified, we'll just use the same directory as the input files.
        output_paths = [i.parent / p.name for (i, p) in zip(input_paths, output_paths)]
    else:
        # If an output directory is specified, we'll use that.
        output_paths = [output_dir / p.name for p in output_paths]

    if len(input_paths) == 0:
        return []

    if isinstance(input_paths, list) and isinstance(input_paths[0], list):
        input_paths = input_paths[0]

    batch_rename_plan = dict(zip(input_paths, output_paths))
    batch_rename(batch_rename_plan, create_backups=create_backups)

    # Simulating the behavior of the "handle_single_or_list" decorator.
    # TODO: This is until I clean it up and remove @handle_single_or_list.
    if isinstance(file_paths, list):
        return dict(zip(input_paths, output_paths))
    return output_paths[0]


def batch_rename(rename_plan: Dict[Path, Path], create_backups: bool = True) -> None:
    input_paths = list(rename_plan.keys())
    output_paths = list(rename_plan.values())

    with concurrent.futures.ProcessPoolExecutor() as executor:
        try:
            results = tqdm(
                executor.map(
                    rename_one_file,
                    input_paths,
                    output_paths,
                    [create_backups] * len(input_paths),
                ),
                total=len(input_paths),
            )
        except KeyboardInterrupt:
            return
        except Exception as e:
            print(e)
            return


def rename_one_file(inp: str, outp: str, create_backup: bool = True):
    """Rename a file. Optionally create a backup of the original file.
    If the output file already exists, the function will do nothing.
    """
    backup_path = None
    inp, outp = Path(inp), Path(outp)
    try:
        if not inp.exists():
            print(f"Input file {inp} does not exist. Skipping.")
            return
        if outp.exists():
            print(f"Output file {outp} already exists. Skipping.")
            return

        if create_backup:
            backup_path = Path(f"{inp}.backup")
            shutil.copy2(inp, backup_path)
        shutil.move(inp, outp)

    except Exception as e:
        print(f"An error occurred when copying {inp} to {outp}: {e}")
        # If an error occurs, rollback the change
        if backup_path and backup_path.exists():
            shutil.move(backup_path, inp)
        raise e


def search_and_rename(
    input_dir: Path,
    output_dir: Path = None,
    create_backups=True,
    recursive=True,
    file_types=None,
    extra_file_types=None,
):
    """Search for files in a directory and rename them."""
    if file_types is None:
        file_types = [".jpg", ".jpeg", ".mp4", ".mov"]
    if extra_file_types is None:
        extra_file_types = [".xmp", ".thm", ".lrv", ".raf"]

    media_files = list_files(input_dir, recursive, file_types)
    extra_files = list_files(input_dir, recursive, extra_file_types)
    suffixless_rename_plan = _get_rename_plan(media_files, return_suffixless=True)
    if not isinstance(suffixless_rename_plan, dict):
        suffixless_rename_plan = {
            media_files[0].with_suffix(""): suffixless_rename_plan
        }

    rename_plan = {}
    for file in media_files + extra_files:
        key = file.with_suffix("")
        if key in suffixless_rename_plan:
            value = suffixless_rename_plan[key].with_suffix(file.suffix)
            rename_plan[file] = value

    # TODO: it's dirty to pass in "None" as file_paths.
    rename(None, output_dir, create_backups, rename_plan)


def list_files(input_dir: Path, recursive=True, file_types=None):
    """List all files in a directory."""
    if file_types is None:
        file_types = [".jpg", ".jpeg", ".mp4", ".mov"]

    file_paths = []
    for file_type in file_types:
        glob_pattern = f"**/*{file_type}" if recursive else f"*{file_type}"
        file_paths.extend(input_dir.glob(glob_pattern))
    return file_paths
