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

    gps_coords = GPSCoordinates.from_exif_metadata(metadatas)
    city_names = gps_coords_to_city_name(gps_coords)
    import ipdb

    ipdb.set_trace()

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


@handle_single_or_list()
def gps_coords_to_city_name(gps_coords: List[GPSCoordinates]) -> List[Union[str, None]]:
    """Get the city name from the GPS coordinates."""
    # reverse_geocoding is expecting all non-None GPSCoordinates.
    # But gps_coords is a list that might contain None values.
    # We need to pre-filter and keep track of the original indexes.

    non_null_indices = [i for i, x in enumerate(gps_coords) if x is not None]
    non_null_gps_coords = [x.to_tuple() for x in gps_coords if x is not None]

    city_names = [None] * len(gps_coords)
    hits = rg.search(non_null_gps_coords)
    for index, hit in zip(non_null_indices, hits):
        city_names[index] = hit["name"]

    return city_names


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
