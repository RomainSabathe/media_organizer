"""Functions for adjusting the capture datetime of media files (photos and videos) based on a source of truth."""
from typing import Union
from pathlib import Path
from datetime import datetime

import exiftool


def get_capture_datetime(file_path: Union[Path, str]) -> datetime:
    # Formatting the filepath and checking existence.
    file_path = Path(file_path)
    if not file_path.exists():
        # ExifTool will raise an error if the file doesn't exist, but this is a more specific error message.
        raise FileNotFoundError(f"File not found: {file_path}")

    # Getting the capture datetime.
    with exiftool.ExifTool() as et:
        metadata = et.execute_json(str(file_path))
        if len(metadata) == 0:
            raise ValueError(f"No metadata found for {file_path}")
        if len(metadata) > 1:
            raise ValueError(f"Found multiple sources of metadata for {file_path}")
        metadata = metadata[0]

        datetime_str = None
        if "EXIF:DateTimeOriginal" in metadata:
            datetime_str = metadata["EXIF:DateTimeOriginal"]
        elif "QuickTime:CreationDate" in metadata:  # For videos
            datetime_str = metadata["QuickTime:CreationDate"]

    # Formatting and returning.
    if datetime_str is not None:
        return datetime.strptime(datetime_str, "%Y:%m:%d %H:%M:%S")
    return None  # Returns None if no capture date was found
