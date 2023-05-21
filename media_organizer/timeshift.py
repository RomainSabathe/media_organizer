"""Functions for adjusting the capture datetime of media files (photos and videos) based on a source of truth."""
from dataclasses import dataclass
from typing import Union, List, Optional, Dict
from pathlib import Path
from datetime import datetime, timezone, timedelta

import exiftool


@dataclass(frozen=True)
class ExifDateTimeField:
    name: str
    has_date_info: bool = True
    has_time_info: bool = True
    has_timezone_info: bool = False
    has_millisecond_info: bool = False
    is_utc: bool = False

    @property
    def format(self) -> str:
        format = ""
        if self.has_date_info:
            format += "%Y:%m:%d"
        if self.has_time_info:
            format += " %H:%M:%S"
            if self.has_millisecond_info:
                format += ".%f"
        if self.has_timezone_info:
            format += "%z"
        return format.strip()

    def parse(self, field_content: str) -> datetime:
        if self.has_timezone_info and not self.is_utc:
            # Sometimes, timezones are expressed like this: +01:00 instead of +0100.
            # We need to convert it to the latter format.
            time_parts, tz_offset_str = (
                field_content.split("+")
                if "+" in field_content
                else field_content.split("-")
            )
            sign = "+" if "+" in field_content else "-"
            tz_offset_str = tz_offset_str.replace(":", "")
            field_content = time_parts + sign + tz_offset_str

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

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, ExifDateTimeTag):
            return self.name == other.name
        return False


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
    ExifDateTimeField(
        "Composite:DateTimeCreated", has_timezone_info=True, is_utc=False
    ),
    ExifDateTimeField("XMP:DateCreated"),
    ExifDateTimeField("XMP:CreateDate"),
    ExifDateTimeField("XMP:DateTimeDigitized", has_timezone_info=True),
    ExifDateTimeField("XMP:DateTimeOriginal", has_timezone_info=True),
    ExifDateTimeField("XMP:GPSDateTime", has_timezone_info=True, is_utc=True),
    ExifDateTimeField("IPTC:DateCreated", has_time_info=False),
    ExifDateTimeField("IPTC:TimeCreated", has_date_info=False, has_timezone_info=True),
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


def determine_timezone(
    file_path: Optional[Union[Path, str]] = None,
    metadata: Optional[Dict[str, str]] = None,
) -> Union[timezone, None]:
    """Determine the timezone of a media file based on its metadata."""
    if file_path is None and metadata is None:
        raise ValueError("Either file_path or metadata must be provided.")
    if metadata is None:
        metadata = extract_metadata_using_exiftool(file_path)

    # Sometimes, we directly have access to fields that have:
    # - timezone info
    # - are *not* expressed in UTC
    # In which case, we can directly use the non-UTC timezone as source of truth.
    for field in DATETIME_FIELDS:
        if (
            field.has_timezone_info
            and not field.is_utc
            and field.name in metadata
            and field.has_date_info
        ):
            return field.parse(metadata[field.name]).tzinfo

    # Otherwise, we need to manually compute the timezone by looking at the difference between
    # naive-datetime and UTC-datetime.
    # We first start by identifying a non-null Exif datetime field that has UTC offset information.
    utc_datetime = None
    for field in DATETIME_FIELDS:
        if (
            not field.has_timezone_info
            or not field.is_utc
            or field.name not in metadata
            or not field.has_date_info
        ):
            continue
        utc_datetime = field.parse(metadata[field.name])
        break
    if utc_datetime is None:
        # For some media (typically: GoPro videos), we simply can't access the timezone
        # info from the datetime fields. Using GPS data is the only other option.
        # TODO: Implement this.
        return None

    # We do the same, this time looking for a field that has no timezone info.
    for field in DATETIME_FIELDS:
        if (
            field.has_timezone_info
            or field.name not in metadata
            or not field.has_date_info
        ):
            continue
        naive_datetime = field.parse(metadata[field.name])
        break

    # We then calculate the difference between the two datetimes.
    diff = naive_datetime - utc_datetime.replace(tzinfo=None)
    return timezone(diff)


def get_capture_datetime(file_path: Union[Path, str]) -> datetime:
    metadata = extract_metadata_using_exiftool(file_path)

    # The presence of one key or another will depend on the nature of the file
    # (photo, video, encoder, etc.) so we greedily find the first one that exists.
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
    metadata = extract_metadata_using_exiftool(file_path)
    media_timezone = determine_timezone(
        metadata=metadata
    )  # Getting timezone info is important
    # because we need to check consistency of datetimes under the same timezone.

    # Here we use a dict to keep track of the mapping between datetime field name
    # and its actual value. It is not needed per se but makes the code
    # more easily debuggable (at the expense of readability).
    datetimes = {}
    for field in DATETIME_FIELDS:
        if field.name in metadata:
            datetimes.update({field: field.parse(metadata[field.name])})

    # We pick an arbitrary datetime (the first) as a reference.
    # We make sure we set it to a timezone-aware datetime.
    # Finally, since some datetimes have microsecond precisions and others don't,
    # we round them to the nearest second.
    datetime_keys = list(datetimes.keys())
    ref_datetime_key = datetime_keys[0]
    ref_datetime = datetimes[ref_datetime_key]
    if ref_datetime.tzinfo is None:
        ref_datetime = ref_datetime.replace(tzinfo=media_timezone)
    else:
        ref_datetime = ref_datetime.astimezone(media_timezone)
    ref_datetime = _nullify_microseconds(ref_datetime)

    # We check that all other datetimes are equal to the reference.
    for datetime_key in datetime_keys[1:]:
        if (
            datetime_key.has_time_info ^ ref_datetime_key.has_time_info
            or datetime_key.has_date_info ^ ref_datetime_key.has_date_info
        ):
            # If one datetime has time info and the other doesn't, we can't compare them.
            # Same for date info.
            continue

        other_datetime = datetimes[datetime_key]
        if other_datetime.tzinfo is None:
            other_datetime = other_datetime.replace(tzinfo=media_timezone)
        else:
            other_datetime = other_datetime.astimezone(media_timezone)
        other_datetime = _nullify_microseconds(other_datetime)

        if other_datetime != ref_datetime:
            return False  # At least one datetime is different

    return True


def set_capture_datetime(
    file_paths: Union[Path, str, List[Union[Path, str]]], new_datetime: datetime
) -> None:
    if not isinstance(file_paths, list):
        file_paths = [file_paths]
    file_paths = [_format_file_path(f) for f in file_paths]

    exiftool_cmd = []
    for field in DATETIME_FIELDS:
        new_datetime_str = field.unparse(new_datetime)
        exiftool_cmd.append(f"-{field.name}={new_datetime_str}")
    exiftool_cmd.extend([str(f) for f in file_paths])
    with exiftool.ExifTool() as et:
        et.execute(*exiftool_cmd)


def shift_capture_datetime(
    file_paths: Union[Path, str, List[Union[Path, str]]],
    datetime_shift: timedelta,
) -> None:
    """
    Shifts the capture datetime of the given file(s) by the given timedelta.
    If no metadata is provided, it will be extracted using ExifTool.

    Args:
        file_paths: The file(s) whose capture datetime will be shifted.
        datetime_shift: The timedelta by which the capture datetime will be shifted.
    """
    if not isinstance(file_paths, list):
        file_paths = [file_paths]
    file_paths = [_format_file_path(f) for f in file_paths]

    exiftool_cmd = []
    # Important note: we *don't* use the "-AllDates+=..." option because it
    # doesn't update some fields (e.g. QuickTime:MediaCreateDate).
    # Explicitely iterating over each identified datetimefield ensures that
    # indeed all fields are updated.
    for field in DATETIME_FIELDS:
        datetime_shift_copy = datetime_shift
        # We must apply special care to the following case (when both of the
        # following conditions are true):
        # 1. The field has no time info (e.g. GPSDateStamp)
        # 2. The timeshift is less than a day.
        # Otherwise, we may end up with surprising results.
        # For instance: 2020-01-01 00:00:00 + (-20 mins) = 2019-12-31 23:40:00
        # We end up shifted by a whole day!
        # The easiest way is to round the shift to the nearest day.
        if not field.has_time_info:
            datetime_shift_copy = timedelta(
                days=round(datetime_shift.total_seconds() / (24 * 60 * 60))
            )

        # new_datetime = field.parse(metadata[field.name]) + datetime_shift_copy
        # new_datetime_str = field.unparse(new_datetime)
        shift_sign = "+=" if datetime_shift_copy.total_seconds() >= 0 else "-="
        datetime_shift_copy = abs(datetime_shift_copy)

        shift_days = datetime_shift_copy.days
        shift_seconds = datetime_shift_copy.seconds
        shift_hours, remainder = divmod(shift_seconds, 3600)
        shift_minutes, shift_seconds = divmod(remainder, 60)

        exiftool_cmd.append(
            # e.g. "-EXIF:DateTimeOriginal+=1 13:02:55"
            # e.g. "-EXIF:DateTimeOriginal-=0 01:20:30"
            f"-{field.name}{shift_sign}{shift_days} {shift_hours:02d}:{shift_minutes:02d}:{shift_seconds:02d}"
        )

    exiftool_cmd.extend([str(f) for f in file_paths])
    with exiftool.ExifTool() as et:
        et.execute(*exiftool_cmd)


def _format_file_path(file_path: Union[Path, str]) -> Path:
    file_path = Path(file_path)
    if not file_path.exists():
        # ExifTool will raise an error if the file doesn't exist, but this is a more specific error message.
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path


def _nullify_microseconds(dt: datetime) -> datetime:
    return dt.replace(microsecond=0)


def _print_all_exif_datetimes(file_path: Union[Path, str]) -> None:
    """Prints all EXIF datetimes found in a file.
    This is useful for debugging purposes."""
    metadata = extract_metadata_using_exiftool(file_path)
    for field in metadata.keys():
        if "time" in field.lower() or "date" in field.lower():
            print(f"{field}: {metadata[field]}")
