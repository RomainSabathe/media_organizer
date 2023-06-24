"""Functions for adjusting the capture datetime of media files (photos and videos) based on a source of truth."""
from pathlib import Path
from dataclasses import dataclass
from typing import Union, List, Optional, Dict, Tuple, Literal
from datetime import time, datetime, timedelta
from datetime import timezone as tz

import pytz
import exiftool
from timezonefinder import TimezoneFinder

from media_organizer.utils import handle_single_or_list


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
            dt = dt.replace(tzinfo=tz.utc)
        return dt

    def unparse(self, date: datetime) -> str:
        if self.has_timezone_info and date.tzinfo is None:
            date = date.replace(tzinfo=tz.utc)
        if self.has_time_info and self.is_utc:
            # Convert to UTC if needed
            date = date.astimezone(tz.utc)
        date_str = date.strftime(self.format)

        # TODO: delete this when we're sure that this is not needed anymore.
        ## ExifTool expects timezones to be expressed like this: +01:00 instead of +0100.
        ## strftime returns the latter format, so we need to convert it to the former.
        # if self.has_timezone_info:
        #    time_parts, tz_offset_str = (
        #        date_str.split("+") if "+" in date_str else date_str.split("-")
        #    )
        #    sign = "+" if "+" in date_str else "-"
        #    tz_offset_str = tz_offset_str[:2] + ":" + tz_offset_str[2:]
        #    date_str = time_parts + sign + tz_offset_str

        return date_str

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, ExifDateTimeField):
            return self.name == other.name
        return False


PHOTO_DATETIME_FIELDS = [
    ExifDateTimeField("EXIF:ModifyDate"),
    ExifDateTimeField("EXIF:DateTimeOriginal"),
    ExifDateTimeField("EXIF:CreateDate"),
    ExifDateTimeField("EXIF:GPSTimeStamp", has_date_info=False),
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
    ExifDateTimeField("XMP:ModifyDate", has_timezone_info=True),
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
    ExifDateTimeField("QuickTime:UTC"),
    ExifDateTimeField(
        "GoPro:GPSDateTime",
        has_timezone_info=False,
        is_utc=True,
        has_millisecond_info=True,
        has_date_info=True,
    ),
]
DATETIME_FIELDS = PHOTO_DATETIME_FIELDS + VIDEO_DATETIME_FIELDS


@dataclass(frozen=True)
class ExifGPSField:
    name: str
    is_embedded: bool = False
    is_longitude: bool = False
    is_latitude: bool = False
    is_altitude: bool = False
    is_multicoords: bool = False

    @staticmethod
    def to_gps_coords(exif_field) -> "GPSCoordinates":
        """Used for the QuickTime:GPSCoords field which is a string
        containing the longitude/latitude information."""
        raise NotImplemented()


GPS_FIELDS = [
    ExifGPSField("EXIF:GPSVersionID"),
    ExifGPSField("EXIF:GPSLatitudeRef"),
    ExifGPSField("EXIF:GPSLatitude", is_latitude=True),
    ExifGPSField("EXIF:GPSLongitudeRef"),
    ExifGPSField("EXIF:GPSLongitude", is_longitude=True),
    ExifGPSField("EXIF:GPSAltitudeRef"),
    ExifGPSField("EXIF:GPSAltitude", is_altitude=True),
    ExifGPSField("EXIF:GPSTimeStamp"),
    ExifGPSField("EXIF:GPSProcessingMethod"),
    ExifGPSField("EXIF:GPSDateStamp"),
    ExifGPSField("EXIF:GPSDifferential"),
    ExifGPSField("QuickTime:GPSCoordinates", is_multicoords=True),
    ExifGPSField("GoPro:GPSMeasureMode", is_embedded=True),
    ExifGPSField("GoPro:GPSDateTime", is_embedded=True),
    ExifGPSField("GoPro:GPSHPositioningError", is_embedded=True),
    ExifGPSField("GoPro:GPSLatitude", is_embedded=True, is_latitude=True),
    ExifGPSField("GoPro:GPSLongitude", is_embedded=True, is_longitude=True),
    ExifGPSField("GoPro:GPSAltitude", is_embedded=True, is_altitude=True),
    ExifGPSField("GoPro:GPSSpeed", is_embedded=True),
    ExifGPSField("GoPro:GPSSpeed3D", is_embedded=True),
]


@handle_single_or_list(is_file_path=True)
def extract_metadata_using_exiftool(
    file_paths: Union[Path, str, List[Union[Path, str]]]
) -> dict:
    with exiftool.ExifTool() as et:
        file_paths_as_str = [str(file_path) for file_path in file_paths]

        # -ee = ExtractEmbedded. Allows to extract metadata from embedded files (e.g. XMP in JPEG)
        exiftool_args = ["-ee", *file_paths_as_str]
        #print(f"Running exiftool with args: {exiftool_args}")
        metadatas = et.execute_json(*exiftool_args)
        if len(metadatas) != len(file_paths):
            raise ValueError(
                f"Expected {len(file_paths)} metadata, got {len(metadatas)}"
            )
    return metadatas


def get_timezone(
    file_path: Optional[Union[Path, str]] = None,
    metadata: Optional[Dict[str, str]] = None,
    based_on_gps: bool = True,
) -> Union[tz, None]:
    """Determine the timezone of a media file based on its metadata.
    -!- Warning: I know for sure this function does *not* have the same behavior
    as Google Photos. Meaning that Google Photos could infer a different datetime
    compared to this function.

    Google Photos has the following behaviour:
    - When GPS info is available, it uses it to determine the timezone.
      In particular, the EXIF:Offset is ignored.
    - Otherwise, it uses fields such as XPM:DateTimeOriginal. Exactly which
      fields are used is still to be determined).
      It works when saving with GeoSetter. GeoSetter sets the
      following fields with timezone info:
      - IPTC:TimeCreated
      - XMP:DateTimeDigitized
      - XMP:DateTimeOriginal
      - XMP:DateCreated
      - XMP:ModifyDate
      - Composite:DateTimeCreated

      Moreover, I verified that Google Photos does *not* use the EXIF:OffsetTime
      field. Once again, this implies that this function has a different behavior
      compared to Google Photos.
      # TODO: try to make this function behave like Google Photos.
    """
    if file_path is None and metadata is None:
        raise ValueError("Either file_path or metadata must be provided.")
    if metadata is None:
        metadata = extract_metadata_using_exiftool(file_path)

    ### There are multiple ways of obtaining the timezone of a media file.
    # In turn, we will try three methods.

    # Method 1: we use the GPS coordinate associated with the file
    # (GooglePhotos does this)
    if based_on_gps:
        try:
            gps_coords = GPSCoordinates.from_exif_metadata(metadata, errors="raise")
            return gps_coords_to_timezone(gps_coords)
        except ValueError:
            # Is raised when there is no GPS information in the file.
            pass

    # Method 2: directly use the timezone info from the metadata.
    if "EXIF:OffsetTime" in metadata:
        offset = metadata["EXIF:OffsetTime"]  # e.g. "+01:00"
        sign = offset[0]
        hours, mins = offset[1:].split(":")
        offset = int(hours) * 60 + int(mins)

        return tz(timedelta(minutes=int(f"{sign}{offset}")))

    # Method 3: we have access to a field that comes with timezone info attached.
    # That is, a field that has:
    # - timezone info
    # - the timezone is *not* expressed in UTC
    # In which case, we can directly use the non-UTC timezone as source of truth.
    for field in DATETIME_FIELDS:
        if (
            field.has_timezone_info
            and not field.is_utc
            and field.name in metadata
            and field.has_date_info
        ):
            return field.parse(metadata[field.name]).tzinfo

    # Method 4: we need to manually compute the timezone by looking at the difference between
    # naive-datetime and UTC-datetime.
    # We first start by identifying a non-null Exif datetime field that has UTC offset information.
    utc_datetime = None
    for field in DATETIME_FIELDS:
        if (
            not field.has_timezone_info
            or not field.is_utc
            or field.name not in metadata
            or not field.has_date_info
            or field.has_millisecond_info  # Miliseconds are irrelevant here
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
            or field.has_millisecond_info
        ):
            continue
        naive_datetime = field.parse(metadata[field.name])
        break

    # We then calculate the difference between the two datetimes.
    diff = naive_datetime - utc_datetime.replace(tzinfo=None)
    return tz(diff)


@handle_single_or_list(is_file_path=True)
def get_capture_datetime(
    file_paths: Union[Path, str, List[Union[Path, str]]],
    with_timezone: bool = False,
    timezone: Union[Literal["local"], Literal["utc"]] = "local",
    force_return_timezone: bool = False,
    metadatas: Optional[List[Dict[str, str]]] = None,
) -> Union[datetime, List[datetime], None, List[None]]:
    if metadatas is None:
        metadatas = extract_metadata_using_exiftool(file_paths)
    if not isinstance(metadatas, list):
        metadatas = [metadatas]

    if timezone != "local":
        raise NotImplementedError
    if not with_timezone and force_return_timezone:
        raise NotImplementedError

    # Embarrassingly parallel. But this is fast given that it's just
    # dictionary lookups.
    return [
        _get_capture_datetime_from_metadata(
            metadata,
            with_timezone=with_timezone,
            force_return_timezone=force_return_timezone,
            timezone=timezone,
        )
        for metadata in metadatas
    ]


def _get_capture_datetime_from_metadata(
    metadata: Dict[str, str],
    with_timezone: bool = False,
    timezone: Union[Literal["local"], Literal["utc"]] = "local",
    force_return_timezone: bool = False,
) -> Union[datetime, None]:
    """Get the capture datetime from a metadata dictionary.
    This function is used internally by get_capture_datetime.
    It will work on a single metadata dictionary (i.e. a single file) whereas
    get_capture_datetime works on a list of files directly.
    """
    # (photo, video, encoder, etc.) so we greedily find the first one that exists.
    exif_field = None  # The Exif field that will be used to get the datetime.
    for field in DATETIME_FIELDS:
        if field.name in metadata:
            exif_field = field
            break

    # Formatting and returning.
    if exif_field is None:
        return None

    capture_datetime = exif_field.parse(metadata[exif_field.name])
    if force_return_timezone:
        capture_datetime = capture_datetime.replace(
            tzinfo=get_timezone(metadata=metadata)
        )
    if not with_timezone:
        capture_datetime = capture_datetime.replace(tzinfo=None)
    return capture_datetime


def capture_datetimes_are_consistent(
    file_path: Union[Path, str], timezone_aware: bool = True
) -> bool:
    """There could be many EXIF fields related to capture datetime. This function checks that they are all consistent."""
    metadata = extract_metadata_using_exiftool(file_path)
    media_timezone = get_timezone(
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
    if timezone_aware:
        if ref_datetime.tzinfo is None:
            ref_datetime = ref_datetime.replace(tzinfo=media_timezone)
        else:
            ref_datetime = ref_datetime.astimezone(media_timezone)
    else:
        ref_datetime = ref_datetime.replace(tzinfo=None)
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
        if timezone_aware:
            if other_datetime.tzinfo is None:
                other_datetime = other_datetime.replace(tzinfo=media_timezone)
            else:
                other_datetime = other_datetime.astimezone(media_timezone)
        else:
            other_datetime = other_datetime.replace(tzinfo=None)
        other_datetime = _nullify_microseconds(other_datetime)

        if abs((other_datetime - ref_datetime).total_seconds()) > 1:
            # If the difference less than 1 second, we still consider the datetimes consistent.
            return False

    return True


def express_video_datetime_as_utc(
    file_path: Path, errors: str = "raise", create_backups: bool = True
) -> None:
    metadata = extract_metadata_using_exiftool(file_path)
    timezone = get_timezone(file_path, metadata=metadata)
    if timezone is None:
        if errors == "raise":
            raise ValueError(f"The file {file_path} has no timezone information.")
        # If the file doesn't have a timezone, we'll use the timezone
        # of the operating system instead.
        timezone = datetime.utcnow().astimezone().tzinfo

    offset = -timezone.utcoffset(datetime.now())
    shift_capture_datetime(
        file_path,
        offset,
        exif_fields=VIDEO_DATETIME_FIELDS,
        create_backups=create_backups,
    )


@handle_single_or_list(is_file_path=True)
def set_capture_datetime(
    file_paths: Union[Path, str, List[Union[Path, str]]],
    new_datetime: datetime,
    create_backups: bool = True,
) -> None:
    """Sets the capture datetime of the given file(s) to the given datetime.
    !! Warning !!: this function will erase the timezone information of the different files.
    The new datetime will be interpreted as UTC.
    To change this, chain this function with `set_timezone`.

    Args:
        file_paths: The file(s) to modify.
        new_datetime: The new datetime to set.
    """
    exiftool_cmd = []
    for field in DATETIME_FIELDS:
        new_datetime_str = field.unparse(new_datetime)
        exiftool_cmd.append(f"-{field.name}={new_datetime_str}")
    if not create_backups:
        exiftool_cmd.append("-overwrite_original")
    exiftool_cmd.extend([str(f) for f in file_paths])
    with exiftool.ExifTool() as et:
        et.execute(*exiftool_cmd)


@handle_single_or_list(is_file_path=True)
def shift_capture_datetime(
    file_paths: Union[Path, str, List[Union[Path, str]]],
    datetime_shift: timedelta,
    create_backups: bool = True,
    exif_fields: Optional[List[ExifDateTimeField]] = None,
) -> None:
    """
    Shifts the capture datetime of the given file(s) by the given timedelta.
    If no metadata is provided, it will be extracted using ExifTool.

    Args:
        file_paths: The file(s) whose capture datetime will be shifted.
        datetime_shift: The timedelta by which the capture datetime will be shifted.
    """
    if exif_fields is None:
        exif_fields = DATETIME_FIELDS

    exiftool_cmd = []
    # Important note: we *don't* use the "-AllDates+=..." option because it
    # doesn't update some fields (e.g. QuickTime:MediaCreateDate).
    # Explicitely iterating over each identified datetimefield ensures that
    # indeed all fields are updated.
    for field in exif_fields:
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

    if not create_backups:
        exiftool_cmd.append("-overwrite_original")
    exiftool_cmd.extend([str(f) for f in file_paths])
    with exiftool.ExifTool() as et:
        et.execute(*exiftool_cmd)


def _nullify_microseconds(dt: datetime) -> datetime:
    return dt.replace(microsecond=0)


def _print_all_exif_datetimes(file_path: Union[Path, str]) -> None:
    """Prints all EXIF datetimes found in a file.
    This is useful for debugging purposes."""
    metadata = extract_metadata_using_exiftool(file_path)
    for field in metadata.keys():
        _field = field.lower().replace("quicktime", "")
        if "time" in _field or "date" in _field or "utc" in _field:
            print(f"{field}: {metadata[field]}")


def _print_all_exif_gps_info(file_path: Union[Path, str]) -> None:
    """Prints all EXIF GPS-related fields found in a file.
    This is useful for debugging purposes."""
    metadata = extract_metadata_using_exiftool(file_path)
    for field in metadata.keys():
        _field = field.lower().replace("quicktime", "")
        if "gps" in _field:
            print(f"{field}: {metadata[field]}")


@handle_single_or_list(is_file_path=True)
def set_timezone(
    file_paths: Union[Path, str, List[Union[Path, str]]],
    timezone: timedelta,
    create_backups: bool = True,
) -> None:
    # TODO: have this function use `timezone` as a `timezone` object instead of a `timedelta`.
    # TODO: the variable name is confusing: we use "timezone", but this corresponds
    #       to the name of a python module (datetime.timezone).
    #       Either we import the module as `tz`, or we rename the variable to `tz`.
    #       Finally, the variable is a timedelta, not a timezone.
    # We need to convert the timezone into "+HH:MM" or "-HH:MM" format.
    # This format will be used by ExifTool.
    if isinstance(timezone, tz):
        # Get a timedelta object representing the offset from UTC
        timezone = timezone.utcoffset(datetime.now())
    hours, remainder = divmod(abs(timezone.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    sign = "-" if timezone.total_seconds() < 0 else "+"
    timezone_str = f"{sign}{int(hours):02d}:{int(minutes):02d}"

    exiftool_cmd = []
    for field in DATETIME_FIELDS:
        if not field.has_timezone_info:
            # We simply take the field and append the timezone info.
            # The line is hard to read because of the escaping, but it's
            # basically:
            # e.g. "-EXIF:ModifyDate<${EXIF:ModifyDate}+08:00"
            arg = f"-{field.name}<$" + "{" + field.name + "}" + timezone_str
        else:
            # When the field already contains the timezone info, we can't simply
            # append another timezone info (we'd end up with "+02:00+08:00").
            # Instead, we perform a string substitution using ExifTool's built-in
            # substitution feature.
            # Again, the line is hard to read because of the escaping, but it's
            # basically:
            # e.g. "-XMP:DateTimeDigitized<${XMP:DateTimeDigitized;s/\+00:00/+08:00/}"
            # TODO: what happens if the timezone info is not "+00:00"?
            arg = (
                f"-{field.name}<$"
                + "{"
                + field.name
                + r";s/\+00:00/"
                + timezone_str
                + "/}"
            )
            arg = f"-{field.name}<$" + "{createdate}" + timezone_str
            exiftool_cmd.append(arg)

    if not create_backups:
        exiftool_cmd.append("-overwrite_original")
    exiftool_cmd.extend([str(f) for f in file_paths])
    with exiftool.ExifTool() as et:
        et.execute(*exiftool_cmd)


@handle_single_or_list(is_file_path=True)
def remove_gps_info(file_paths: Union[Path, str, List[Union[Path, str]]]):
    """Removes all GPS-related EXIF fields from a file.

    This function will raise an error if the file contains any embedded GPS data.
    Embedded GPS can arise for instance in GoPro videos. Those can't be
    deleted from the file using ExifTool.
    """
    # First we read what GPS fields are available to understand if all of them
    # can be removed.
    # TODO: expand the extract_metadata_using_exiftool function to return
    # a list of dicts (1 per input file).
    metadata = extract_metadata_using_exiftool(file_paths[0])
    has_gps_info = False  # If there's no GPS info, we don't need to do anything.
    for gps_field in GPS_FIELDS:
        if gps_field.name in metadata:
            has_gps_info = True
            if gps_field.is_embedded:
                raise ProtectedExifAttributes(
                    f"Can't remove {gps_field.name} because it's an embedded attribute."
                )
    if not has_gps_info:
        return

    exiftool_cmd = []
    for field in GPS_FIELDS:
        exiftool_cmd.append(f"-{field.name}=")

    exiftool_cmd.extend([str(f) for f in file_paths])
    with exiftool.ExifTool() as et:
        et.execute(*exiftool_cmd)


@dataclass
class GPSCoordinates:
    latitude: float
    longitude: float

    def to_tuple(self) -> Tuple[float, float]:
        return (self.latitude, self.longitude)

    @staticmethod
    @handle_single_or_list(is_embarrassingly_parallel=True)
    def from_exif_metadata(
        metadata: Dict[str, str], errors: str = "ignore"
    ) -> "GPSCoordinates":
        latitude, longitude = None, None
        for field in GPS_FIELDS:
            if field.name not in metadata:
                continue
            if field.is_latitude:
                latitude = metadata.get(field.name)
            if field.is_longitude:
                longitude = metadata.get(field.name)

        if latitude is None or longitude is None:
            if errors == "ignore":
                return None
            raise ValueError("Metadata does not contain GPS information")

        return GPSCoordinates(latitude, longitude)


@handle_single_or_list(is_embarrassingly_parallel=True)
def gps_coords_to_timezone(coords: GPSCoordinates) -> datetime:
    if coords is None:
        return None

    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=coords.longitude, lat=coords.latitude)
    if timezone_str is None:
        raise UnknownTimezone()
    pytz_timezone = pytz.timezone(timezone_str)

    # Converting to datetime
    now = datetime.now(pytz_timezone)
    offset_seconds = now.utcoffset().total_seconds()
    offset_hours = offset_seconds / 3600

    return tz(timedelta(hours=offset_hours))


class ProtectedExifAttributes(Exception):
    """Some EXIF metadata are so-called embedded. To access them, we need
    to use the -ee argument of ExifTool. This allows us to _read_ the attribute,
    but not to _set_ it.
    When the user is trying to do that (for instance when removing GPS info),
    we raise this exception."""

    pass


class UnknownTimezone(Exception):
    pass


def shift_capture_datetime_to_target(
    file_paths: Union[Path, str, List[Union[Path, str]]],
    reference_img: Union[Path, str],
    target_time: Union[time, datetime],
):
    """Computes the timedelta between the capture datetime of the reference file
    and the target and applies this delta to the filepaths.

    A typical scenario for using this function is the following:
        - you take a picture of a clock with your camera (`reference_img`)
        - the camera may have a slightly different time than the clock, but we assume
          that the clock has the correct time (`target_time`).
        - you also took a bunch of pictures with your camera (`file_paths`)
        - therefore you want to shift the capture datetime of all the pictures
          to match the clock's time.
    """
    # Calculting the datetime delta to apply.
    ref_datetime = get_capture_datetime(reference_img).replace(tzinfo=None)
    # We need to transform `target_time` to a datetime object (if it's not already)
    # For this, we give it the same day as the reference file.
    if not isinstance(target_time, datetime):
        target_time = datetime.combine(ref_datetime, target_time)
    if target_time.second == 0:
        # If the target_time doesn't have seconds, we add them.
        # Otherwise, the resulting datetime will be like HH:MM:00
        # And we want the seconds to be preserved.
        target_time = target_time.replace(second=ref_datetime.second)
    delta = target_time - ref_datetime

    shift_capture_datetime(file_paths, delta)
