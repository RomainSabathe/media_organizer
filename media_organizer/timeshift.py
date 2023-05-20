"""Functions for adjusting the capture datetime of media files (photos and videos) based on a source of truth."""
from typing import Union
from pathlib import Path
from datetime import datetime

import exiftool

# Order matters.
PHOTO_DATETIME_KEYS = [
    "EXIF:ModifyDate",
    "EXIF:DateTimeOriginal",
    "EXIF:CreateDate",
    "EXIF:CreateDate",
    "Composite:SubSecCreateDate",  # Contains sub-milisecond info
    "Composite:SubSecDateTimeOriginal",  # Contains sub-milisecond info
    "Composite:SubSecModifyDate",  # Contains sub-milisecond info
    "Composite:GPSDateTime",  # Contains timezone info
]
PHOTO_DATE_KEYS = [
    "EXIF:GPSDateStamp",
]
VIDEO_DATETIME_KEYS = [
    "QuickTime:CreateDate",
    "QuickTime:ModifyDate",
    "QuickTime:TrackCreateDate",
    "QuickTime:TrackModifyDate",
    "QuickTime:MediaCreateDate",
    "QuickTime:MediaModifyDate",
]
DATETIME_KEYS = PHOTO_DATETIME_KEYS + VIDEO_DATETIME_KEYS


def get_capture_datetime(file_path: Union[Path, str]) -> datetime:
    file_path = _format_file_path(file_path)

    # Getting the capture datetime.
    with exiftool.ExifTool() as et:
        metadata = et.execute_json(str(file_path))
        if len(metadata) == 0:
            raise ValueError(f"No metadata found for {file_path}")
        if len(metadata) > 1:
            raise ValueError(f"Found multiple sources of metadata for {file_path}")
        metadata = metadata[0]

        # The presence of one key or another will depend on the nature of the file
        # (photo, video, encoder, etc.) so we greedily find the first one that exists.
        datetime_str = None
        for key in DATETIME_KEYS:
            if key in metadata:
                datetime_str = metadata[key]
                break

    # Formatting and returning.
    if datetime_str is not None:
        return datetime.strptime(datetime_str, "%Y:%m:%d %H:%M:%S")
    return None  # Returns None if no capture date was found


def set_capture_datetime(file_path: Union[Path, str], new_datetime: datetime) -> None:
    file_path = _format_file_path(file_path)

    new_datetime_str = new_datetime.strftime("%Y:%m:%d %H:%M:%S")
    with exiftool.ExifTool() as et:
        et.execute(
            f"-EXIF:ModifyDate={new_datetime_str}",
            f"-QuickTime:CreateDate={new_datetime_str}",
            str(file_path),
        )


def _format_file_path(file_path: Union[Path, str]) -> Path:
    file_path = Path(file_path)
    if not file_path.exists():
        # ExifTool will raise an error if the file doesn't exist, but this is a more specific error message.
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path
