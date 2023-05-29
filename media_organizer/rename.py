from pathlib import Path
from typing import List, Union, Dict, Optional

import reverse_geocoder as rg

from media_organizer.utils import handle_single_or_list
from media_organizer.timeshift import (
    extract_metadata_using_exiftool,
    get_capture_datetime,
    GPSCoordinates,
    get_timezone,
)


@handle_single_or_list(is_file_path=True)
def rename(file_paths: Union[Path, str, List[Union[Path, str]]]) -> List[Path]:
    """Rename a file or a list of files with the following format:
    <date>-<city>-<device>.<extension>
    <date> is the capture datetime of the file in ISO 8601 format.
    <city> is the city where the file was captured (if GPS info is available).
    <device> is the device used to capture the file.
    <extension> is the file extension.
    """
    # Part 1: capture datetime.
    metadatas = extract_metadata_using_exiftool(file_paths)
    capture_datetimes = get_capture_datetime(file_paths, force_return_timezone=True)
    if not isinstance(capture_datetimes, list):
        capture_datetimes = [capture_datetimes]

    # Part 2: city name
    gps_coords = GPSCoordinates.from_exif_metadata(metadatas)
    city_names = gps_coords_to_city_name(gps_coords)
    if not isinstance(city_names, list):
        city_names = [city_names]

    # Part 3: device name
    device_names = extract_device_name_from_metadata(metadatas)
    if not isinstance(device_names, list):
        device_names = [device_names]

    # Now putting it all together
    new_names = []
    iterator = zip(file_paths, capture_datetimes, city_names, device_names)
    for file_path, *info_triplet in iterator:
        info_triplet = [part for part in info_triplet if part is not None]
        # The first element should always be there: it's the capture datetime.
        info_triplet[0] = info_triplet[0].isoformat()
        new_name = Path("-".join(info_triplet)).with_suffix(file_path.suffix)
        new_names.append(new_name)

    return new_names


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

    return "_".join(parts)
