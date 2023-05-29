from pathlib import Path
from typing import List, Union, Dict

import reverse_geocoder as rg

from media_organizer.utils import handle_file_path_as_singleton_or_list
from media_organizer.timeshift import (
    extract_metadata_using_exiftool,
    get_capture_datetime,
    GPSCoordinates,
    get_timezone,
)


@handle_file_path_as_singleton_or_list
def rename(file_paths: Union[Path, str, List[Union[Path, str]]]) -> Path:
    """Rename a file or a list of files with the following format:
    <date>-<city>-<device>.<extension>
    <date> is the capture datetime of the file in ISO 8601 format.
    <city> is the city where the file was captured (if GPS info is available).
    <device> is the device used to capture the file.
    <extension> is the file extension.
    """
    new_name_parts = []

    metadatas = extract_metadata_using_exiftool(file_paths)
    capture_datetimes = get_capture_datetime(file_paths, force_return_timezone=True)
    new_name_parts.append(capture_datetime.isoformat())

    try:
        gps_coords = GPSCoordinates.from_exif_metadata(metadata)
        if gps_coords:
            hits = rg.search(gps_coords.to_tuple())
            city_name = hits[0]["name"]
            new_name_parts.append(city_name)
    except ValueError:
        # The file doesn't have GPS info.
        pass

    device_name = extract_device_name_from_metadata(metadata)
    if device_name:
        new_name_parts.append(device_name)

    new_name = "-".join(new_name_parts)
    return Path(new_name).with_suffix(file_path.suffix)


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
