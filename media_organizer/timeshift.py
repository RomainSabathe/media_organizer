"""Functions for adjusting the capture datetime of media files (photos and videos) based on a source of truth."""
from dataclasses import dataclass
from typing import Union, List
from pathlib import Path
from datetime import datetime, timezone, timedelta

import exiftool


@dataclass
class ExifDateTimeField:
    name: str
    has_time_info: bool = True
    has_timezone_info: bool = False
    has_millisecond_info: bool = False
    is_utc: bool = False

    @property
    def format(self) -> str:
        format = "%Y:%m:%d"
        if self.has_time_info:
            format += " %H:%M:%S"
            if self.has_millisecond_info:
                format += ".%f"
        if self.has_timezone_info:
            format += "%z"
        return format

    def parse(self, field_content: str) -> datetime:
        dt = datetime.strptime(field_content, self.format)
        if self.has_timezone_info and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def unparse(self, date: datetime) -> str:
        if self.has_timezone_info and date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        if self.has_time_info and self.is_utc:
            # Convert to UTC if needed
            date = date.astimezone(timezone.utc)
        return date.strftime(self.format)


# Order matters.
PHOTO_DATETIME_FIELDS = [
    ExifDateTimeField("EXIF:ModifyDate"),
    ExifDateTimeField("EXIF:DateTimeOriginal"),
    ExifDateTimeField("EXIF:CreateDate"),
    ExifDateTimeField("EXIF:GPSDateStamp", has_time_info=False),
    ExifDateTimeField("Composite:SubSecCreateDate", has_millisecond_info=True),
    ExifDateTimeField("Composite:SubSecDateTimeOriginal", has_millisecond_info=True),
    ExifDateTimeField("Composite:SubSecModifyDate", has_millisecond_info=True),
    ExifDateTimeField("Composite:GPSDateTime", has_timezone_info=True, is_utc=True),
    ExifDateTimeField("Composite:GPSDateTimeCreated", has_timezone_info=True),
    ExifDateTimeField("XMP:DateTimeDigitized", has_timezone_info=True),
    ExifDateTimeField("XMP:DateTimeOriginal", has_timezone_info=True),
    ExifDateTimeField("XMP:GPSDateTime", has_timezone_info=True, is_utc=True),
]
VIDEO_DATETIME_FIELDS = [
    ExifDateTimeField("QuickTime:CreateDate"),
    ExifDateTimeField("QuickTime:ModifyDate"),
    ExifDateTimeField("QuickTime:TrackCreateDate"),
    ExifDateTimeField("QuickTime:TrackModifyDate"),
    ExifDateTimeField("QuickTime:MediaCreateDate"),
    ExifDateTimeField("QuickTime:MediaModifyDate"),
]
DATETIME_FIELDS = PHOTO_DATETIME_FIELDS + VIDEO_DATETIME_FIELDS


def extract_metadata_using_exiftool(file_path: Union[Path, str]) -> dict:
    file_path = _format_file_path(file_path)

    with exiftool.ExifTool() as et:
        metadata = et.execute_json(str(file_path))
        if len(metadata) == 0:
            raise ValueError(f"No metadata found for {file_path}")
        if len(metadata) > 1:
            raise ValueError(f"Found multiple sources of metadata for {file_path}")
        metadata = metadata[0]
    return metadata


def determine_timezone(file_path: Union[Path, str]) -> timezone:
    file_path = _format_file_path(file_path)
    metadata = extract_metadata_using_exiftool(file_path)

    # We first start by identifying a non-null Exif datetime field that has UTC offset information.
    for field in DATETIME_FIELDS:
        if (
            not field.has_timezone_info and not field.is_utc
        ) or field.name not in metadata:
            continue
        utc_datetime = field.parse(metadata[field.name])

    # We do the same, this time looking for a field that has no timezone info.
    for field in DATETIME_FIELDS:
        if field.has_timezone_info or field.name not in metadata:
            continue
        naive_datetime = field.parse(metadata[field.name])

    # We then calculate the difference between the two datetimes.
    diff = naive_datetime - utc_datetime.replace(tzinfo=None)
    # To avoid awkward offsets, we need to round the time difference so that
    # it is a multiple of 3600 seconds (1 hour).
    diff = timedelta(hours=round(diff.total_seconds() / 3600))
    return timezone(diff)

    # la = timezone(diff)
    # print(naive_datetime)
    # print(naive_datetime.replace(tzinfo=la))
    # print(naive_datetime.replace(tzinfo=la).astimezone(timezone.utc))
    # import ipdb

    # ipdb.set_trace()


def get_capture_datetime(file_path: Union[Path, str]) -> datetime:
    file_path = _format_file_path(file_path)
    metadata = extract_metadata_using_exiftool(file_path)

    # The presence of one key or another will depend on the nature of the file
    # (photo, video, encoder, etc.) so we greedily find the first one that exists.
    datetime_str = None
    for field in metadata.keys():
        # for field in DATETIME_FIELDS:
        # if field.name in metadata:
        if "time" in field.lower():
            print(field, metadata[field])

    import ipdb

    ipdb.set_trace()

    field1 = ExifDateTimeField("EXIF:DateTimeOriginal")
    field2 = ExifDateTimeField("Composite:GPSDateTime", has_timezone_info=True)
    val1 = metadata[field1.name]
    val2 = metadata[field2.name]

    val1 = field1.parse(val1)
    val2 = field2.parse(val2)

    val2 = val2.astimezone(timezone.utc).replace(tzinfo=None)
    print(val1, val2)
    diff = val1 - val2
    print(field1.unparse(val1.astimezone(timezone(diff))))
    print(field2.unparse(val2.astimezone(timezone(diff))))
    exif_field = None  # The Exif field that will be used to get the datetime.
    for field in DATETIME_FIELDS:
        if field.name in metadata:
            exif_field = field
            break

    # Formatting and returning.
    if exif_field is not None:
        return exif_field.parse(metadata[exif_field.name])
    return None  # Returns None if no capture date was found


def capture_datetimes_are_consistent(file_path: Union[Path, str]) -> bool:
    """There could be many EXIF fields related to capture datetime. This function checks that they are all consistent."""
    file_path = _format_file_path(file_path)
    metadata = extract_metadata_using_exiftool(file_path)

    datetimes = {}
    for field in DATETIME_FIELDS:
        if field.name in metadata:
            datetimes.update({field.name: field.parse(metadata[field.name])})

    datetime_keys = list(datetimes.keys())
    ref_datetime = datetimes[datetime_keys[0]]
    # This way of writing is verbose, but allows for easier debugging.
    for datetime_key in datetime_keys[1:]:
        if datetimes[datetime_key] != ref_datetime:
            return False  # At least one datetime is different
    return True


def set_capture_datetime(
    file_paths: Union[Path, str, List[Union[Path, str]]], new_datetime: datetime
) -> None:
    if not isinstance(file_paths, list):
        file_paths = [file_paths]
    file_paths = [_format_file_path(f) for f in file_paths]

    new_datetime_str = new_datetime.strftime("%Y:%m:%d %H:%M:%S")
    exiftool_cmd = [f"-{key}={new_datetime_str}" for key in DATETIME_FIELDS]
    exiftool_cmd.extend([str(f) for f in file_paths])
    with exiftool.ExifTool() as et:
        et.execute(*exiftool_cmd)


def _format_file_path(file_path: Union[Path, str]) -> Path:
    file_path = Path(file_path)
    if not file_path.exists():
        # ExifTool will raise an error if the file doesn't exist, but this is a more specific error message.
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path
