from datetime import time, datetime, timezone, timedelta

import pytest

from media_organizer.rename import extract_device_name_from_metadata
from media_organizer.timeshift import (
    GPSCoordinates,
    PHOTO_DATETIME_FIELDS,
    ProtectedExifAttributes,
    VIDEO_DATETIME_FIELDS,
    ExifDateTimeField,
    _print_all_exif_datetimes,
    _print_all_exif_gps_info,
    capture_datetimes_are_consistent,
    express_video_datetime_as_utc,
    extract_metadata_using_exiftool,
    get_capture_datetime,
    get_timezone,
    gps_coords_to_timezone,
    remove_gps_info,
    set_capture_datetime,
    set_timezone,
    shift_capture_datetime,
    shift_capture_datetime_to_target,
)


def datetime_approx_equal(dt1, dt2, delta=60):
    return abs(dt1 - dt2).total_seconds() <= delta


def test_extract_metadata_multiple_files(test_img_phone, test_img_camera):
    metadatas = extract_metadata_using_exiftool([test_img_phone, test_img_camera])
    assert len(metadatas) == 2

    phone_name = extract_device_name_from_metadata(metadatas[0])
    assert phone_name == "Huawei_VOG-L09"

    camera_name = extract_device_name_from_metadata(metadatas[1])
    assert camera_name == "Fujifilm_X-T20"


def test_get_capture_datetime_photo_phone(test_img_phone):
    expected_datetime = datetime(2023, 5, 17, 9, 30, 3)
    assert get_capture_datetime(test_img_phone) == expected_datetime
    assert capture_datetimes_are_consistent(test_img_phone)


def test_get_capture_datetime_vid_phone():
    assert False


def test_get_capture_datetime_photo_camera(test_img_camera):
    expected_datetime = datetime(2019, 12, 17, 12, 3, 24)
    assert get_capture_datetime(test_img_camera) == expected_datetime
    assert capture_datetimes_are_consistent(test_img_camera)


def test_get_capture_datetime_video_camera(test_vid_camera):
    expected_datetime = datetime(2023, 6, 2, 22, 35, 12)
    assert get_capture_datetime(test_vid_camera) == expected_datetime
    # For some reason, the QuickTime tags are 26 seconds ahead the
    # EXIF: tags.
    # This test will fail at this stage.
    # TODO: investigate.
    assert capture_datetimes_are_consistent(test_vid_camera)


def test_get_capture_datetime_video_gopro(test_vid_gopro):
    expected_datetime = datetime(2023, 6, 23, 16, 7, 15)
    assert get_capture_datetime(test_vid_gopro) == expected_datetime
    assert capture_datetimes_are_consistent(test_vid_gopro)


def test_get_capture_datetime_batch(test_img_phone, test_img_camera, test_vid_gopro):
    capture_datetimes = get_capture_datetime(
        [test_img_phone, test_img_camera, test_vid_gopro]
    )
    assert capture_datetimes == [
        datetime(2023, 5, 17, 9, 30, 3),
        datetime(2019, 12, 17, 12, 3, 24),
        datetime(2023, 6, 23, 16, 7, 15),
    ]


def test_set_capture_datetime_one_at_a_time(test_media_file):
    old_date = get_capture_datetime(test_media_file)
    new_date = datetime(2023, 5, 20, 15, 20, 33)
    assert old_date != new_date

    set_capture_datetime(test_media_file, new_date)
    assert get_capture_datetime(test_media_file) == new_date
    # Setting a capture datetime removes the original timezone information
    # (recall that at the moment, we can't set a datetime *and* a timezone
    # at the same time, nor can we set an arbitrary datetime while keeping
    # the original timezone information).
    # Hence we need to check consistency without timezone awareness.
    assert capture_datetimes_are_consistent(test_media_file, timezone_aware=False)


def test_set_capture_datetime_many_at_a_time(test_media_files):
    old_dates = [get_capture_datetime(f) for f in test_media_files]
    new_date = datetime(2023, 5, 20, 15, 20, 33)
    assert all([old_date != new_date for old_date in old_dates])

    set_capture_datetime(test_media_files, new_date)
    assert all([get_capture_datetime(f) == new_date for f in test_media_files])
    assert all(
        [
            capture_datetimes_are_consistent(f, timezone_aware=False)
            for f in test_media_files
        ]
    )


def test_shift_capture_datetime_photo_phone(test_img_phone):
    # From a previous test, we know that the original date is 2023-05-17 09:30:03.
    datetime_shift = timedelta(hours=-2, minutes=47, seconds=13)
    expected_datetime = datetime(2023, 5, 17, 8, 17, 16)
    shift_capture_datetime(test_img_phone, datetime_shift)

    assert get_capture_datetime(test_img_phone) == expected_datetime
    assert capture_datetimes_are_consistent(test_img_phone)


def test_shift_capture_datetime_photo_camera(test_img_camera):
    # From a previous test, we know that the original date  is 2019-12-17 12:03:24.
    datetime_shift = timedelta(hours=-2, minutes=47, seconds=13)
    expected_datetime = datetime(2019, 12, 17, 10, 50, 37)

    shift_capture_datetime(test_img_camera, datetime_shift)
    assert get_capture_datetime(test_img_camera) == expected_datetime
    assert capture_datetimes_are_consistent(test_img_camera)


def test_shift_capture_datetime_video_camera(test_vid_camera):
    # From a previous test, we know that the original date  is 2023-06-02 22:35:12.
    datetime_shift = timedelta(hours=-2, minutes=47, seconds=13)
    expected_datetime = datetime(2023, 6, 2, 21, 22, 25)

    shift_capture_datetime(test_vid_camera, datetime_shift)
    assert get_capture_datetime(test_vid_camera) == expected_datetime
    # TODO: this will fail.
    assert capture_datetimes_are_consistent(test_vid_camera)


def test_shift_capture_datetime_photo_phone_positive_shift(test_img_phone):
    # From a previous test, we know that the original date is 2023-05-17 09:30:03.
    datetime_shift = timedelta(hours=3, minutes=-5, seconds=13)
    expected_datetime = datetime(2023, 5, 17, 12, 25, 16)

    shift_capture_datetime(test_img_phone, datetime_shift)
    assert get_capture_datetime(test_img_phone) == expected_datetime
    assert capture_datetimes_are_consistent(test_img_phone)


def test_shift_capture_datetime_photo_camera_positive_shift(test_img_camera):
    # From a previous test, we know that the original date  is 2019-12-17 12:03:24.
    datetime_shift = timedelta(hours=3, minutes=-5, seconds=13)
    expected_datetime = datetime(2019, 12, 17, 14, 58, 37)

    shift_capture_datetime(test_img_camera, datetime_shift)
    assert get_capture_datetime(test_img_camera) == expected_datetime
    assert capture_datetimes_are_consistent(test_img_camera)


def test_shift_capture_datetime_video_camera_positive_shift(test_vid_camera):
    # From a previous test, we know that the original date  is 2023-06-02 22:35:12.
    datetime_shift = timedelta(hours=3, minutes=-5, seconds=13)
    expected_datetime = datetime(2023, 6, 3, 1, 30, 25)

    shift_capture_datetime(test_vid_camera, datetime_shift)
    assert get_capture_datetime(test_vid_camera) == expected_datetime
    # TODO: this will fail.
    assert capture_datetimes_are_consistent(test_vid_camera)


def test_shift_capture_datetime_video_gopro(test_vid_gopro):
    # From a previous test, we know that original date is 2023-06-23 16:07:15
    datetime_shift = timedelta(hours=-2, minutes=47, seconds=13)
    expected_datetime = datetime(2023, 6, 23, 14, 54, 28)

    shift_capture_datetime(test_vid_gopro, datetime_shift)
    assert get_capture_datetime(test_vid_gopro) == expected_datetime
    assert capture_datetimes_are_consistent(test_vid_gopro)


def test_shift_capture_datetime_video_positive_shift(test_vid_gopro):
    # From a previous test, we know that original date is 2023-06-23 16:07:15
    datetime_shift = timedelta(hours=3, minutes=-5, seconds=13)
    expected_datetime = datetime(2023, 6, 23, 19, 2, 28)

    shift_capture_datetime(test_vid_gopro, datetime_shift)
    assert get_capture_datetime(test_vid_gopro) == expected_datetime
    assert capture_datetimes_are_consistent(test_vid_gopro)


def test_shift_capture_datetime_many_at_a_time(
    test_img_phone, test_img_camera, test_vid_gopro
):
    # See previous tests for explanation of these dates.
    expected_date_img_phone = datetime(2023, 5, 17, 8, 17, 16)
    expected_date_img_camera = datetime(2019, 12, 17, 10, 50, 37)
    expected_date_vid = datetime(2023, 6, 23, 14, 54, 28)
    datetime_shift = timedelta(hours=-2, minutes=47, seconds=13)

    shift_capture_datetime(
        [test_img_phone, test_img_camera, test_vid_gopro], datetime_shift
    )
    assert get_capture_datetime(test_img_phone) == expected_date_img_phone
    assert get_capture_datetime(test_img_camera) == expected_date_img_camera
    assert get_capture_datetime(test_vid_gopro) == expected_date_vid
    assert capture_datetimes_are_consistent(test_img_phone)
    assert capture_datetimes_are_consistent(test_img_camera)
    assert capture_datetimes_are_consistent(test_vid_gopro)


def test_shift_capture_datetime_many_at_a_time_positive_shift(
    test_img_phone, test_img_camera, test_vid_gopro
):
    # See previous tests for explanation of these dates.
    expected_date_img_phone = datetime(2023, 5, 17, 12, 25, 16)
    expected_date_img_camera = datetime(2019, 12, 17, 14, 58, 37)
    expected_date_vid = datetime(2023, 6, 23, 19, 2, 28)
    datetime_shift = timedelta(hours=3, minutes=-5, seconds=13)

    shift_capture_datetime(
        [test_img_phone, test_img_camera, test_vid_gopro], datetime_shift
    )
    assert get_capture_datetime(test_img_phone) == expected_date_img_phone
    assert get_capture_datetime(test_img_camera) == expected_date_img_camera
    assert get_capture_datetime(test_vid_gopro) == expected_date_vid
    assert capture_datetimes_are_consistent(test_img_phone)
    assert capture_datetimes_are_consistent(test_img_camera)
    assert capture_datetimes_are_consistent(test_vid_gopro)


def test_get_timezone_img_phone(test_img_phone):
    assert get_timezone(test_img_phone) == timezone(timedelta(seconds=7200))


def test_get_timezone_img_camera(test_img_camera):
    assert get_timezone(test_img_camera) == timezone(timedelta(hours=2))


def test_get_timezone_video_camera(test_vid_camera):
    assert get_timezone(test_vid_camera) == None


def test_get_timezone_video_gopro(test_vid_gopro):
    assert get_timezone(test_vid_gopro) == timezone(timedelta(hours=2))


# We test both positive and negative timezone shifts.
@pytest.mark.parametrize("new_timezone", [timedelta(hours=6), timedelta(hours=-8)])
def test_set_timezone_img_phone(test_img_phone, new_timezone):
    expected_datetime = datetime(2023, 5, 17, 9, 30, 3)
    assert get_capture_datetime(test_img_phone) == expected_datetime

    set_timezone(test_img_phone, new_timezone)
    # we use based_on_gps=False because presence of GPS information will dominate
    # the estimate of the timezone information. This is how Google Photos work.
    assert get_timezone(test_img_phone, based_on_gps=False) == timezone(new_timezone)
    assert get_capture_datetime(test_img_phone) == expected_datetime


# We test both positive and negative timezone shifts.
@pytest.mark.parametrize("new_timezone", [timedelta(hours=6), timedelta(hours=-8)])
def test_set_timezone_video_camera(test_vid_camera, new_timezone):
    expected_datetime = datetime(2023, 6, 2, 22, 35, 12)
    assert get_capture_datetime(test_vid_camera) == expected_datetime

    set_timezone(test_vid_camera, new_timezone)
    assert get_timezone(test_vid_camera) == timezone(new_timezone)
    assert get_capture_datetime(test_vid_camera) == expected_datetime


# We test both positive and negative timezone shifts.
@pytest.mark.parametrize("new_timezone", [timedelta(hours=6), timedelta(hours=-8)])
def test_set_timezone_video_gopro(test_vid_gopro, new_timezone):
    expected_datetime = datetime(2023, 6, 23, 16, 7, 15)
    assert get_capture_datetime(test_vid_gopro) == expected_datetime

    set_timezone(test_vid_gopro, new_timezone)
    # TODO: this will fail. Need to investigate.
    assert get_timezone(test_vid_gopro, based_on_gps=False) == timezone(new_timezone)
    assert get_capture_datetime(test_vid_gopro) == expected_datetime


def test_google_photos(test_img_phone, test_vid_gopro):
    assert True
    # # test_img_phone = (
    # #    "C:/Users/RSaba/git/media_organizer/tests/data/tmp/test_img_phone.jpg"
    # # )
    # test_img_phone = test_vid_gopro
    # set_capture_datetime(test_img_phone, datetime(2023, 5, 21, 16, 10, 00))
    # remove_gps_info(test_img_phone)
    # # _print_all_exif_datetimes(test_img_phone)
    # set_timezone(test_img_phone, timedelta(hours=8))
    # _print_all_exif_datetimes(test_img_phone)


def test_determine_timezone_depending_on_availability_of_gps(test_img_phone):
    assert timezone(timedelta(hours=2)) == get_timezone(test_img_phone)

    # Now, even if we manually set a new timezone, the `determine_timezone` function
    # should still return UTC+2. That's because we rely on the GPS information
    # which still points to UTC+2.
    # That's the observed behaviour of Google Photos.
    set_timezone(test_img_phone, timedelta(hours=8))
    assert timezone(timedelta(hours=2)) == get_timezone(test_img_phone)

    # Once we remove GPS info, the method should return UTC+8.
    remove_gps_info(test_img_phone)
    assert timezone(timedelta(hours=8)) == get_timezone(test_img_phone)


def test_remove_gps_info_photos(test_img):
    gps_fields = ["EXIF:GPSLongitude", "QuickTime:GPSCoordinates", "GoPro:GPSLatitude"]

    metadata = extract_metadata_using_exiftool(test_img)
    if all([metadata.get(gps_field) is None for gps_field in gps_fields]):
        # The file didn't have any GPS info to begin with.
        return
    assert any([metadata.get(gps_field) is not None for gps_field in gps_fields])

    remove_gps_info(test_img)
    metadata = extract_metadata_using_exiftool(test_img)
    assert all([metadata.get(gps_field) is None for gps_field in gps_fields])


def test_remove_gps_info_video_gopro(test_vid_gopro):
    # We can't remove GPS info from GoPro videos because it's stored in an
    # embedded field of Exif metadata.
    with pytest.raises(ProtectedExifAttributes):
        remove_gps_info(test_vid_gopro)


def test_get_timezone_from_gps_coords_img_phone(test_img_phone):
    metadata = extract_metadata_using_exiftool(test_img_phone)
    extracted_timezone = gps_coords_to_timezone(
        GPSCoordinates.from_exif_metadata(metadata)
    )
    expected_timezone = timezone(timedelta(hours=2))
    assert extracted_timezone == expected_timezone


def test_get_timezone_from_gps_coords_img_camera(test_img_camera):
    metadata = extract_metadata_using_exiftool(test_img_camera)
    with pytest.raises(ValueError):
        # We have no GPS info on most camera files.
        extracted_timezone = gps_coords_to_timezone(
            GPSCoordinates.from_exif_metadata(metadata, errors="raise")
        )

    extracted_timezone = gps_coords_to_timezone(
        GPSCoordinates.from_exif_metadata(metadata, errors="ignore")
    )
    assert extracted_timezone is None


def test_get_timezone_from_gps_coords_vid(test_vid_gopro):
    metadata = extract_metadata_using_exiftool(test_vid_gopro)
    extracted_timezone = gps_coords_to_timezone(
        GPSCoordinates.from_exif_metadata(metadata)
    )
    expected_timezone = timezone(timedelta(hours=+3))  # Madagascar


def test_get_timezone_from_gps_coords_batch(
    test_img_phone, test_img_camera, test_vid_gopro
):
    metadatas = extract_metadata_using_exiftool(
        [test_img_phone, test_img_camera, test_vid_gopro]
    )
    gps_coords = GPSCoordinates.from_exif_metadata(metadatas)
    extracted_timezones = gps_coords_to_timezone(gps_coords)

    assert extracted_timezones[0] == timezone(timedelta(hours=+2))
    assert extracted_timezones[1] is None
    assert extracted_timezones[2] == timezone(timedelta(hours=+2))


def test_shift_capture_datetime_to_target_trivial(test_img_camera_watch):
    """In this test, the reference and the list of images to shift are the same."""
    # The watch indicates "21:03"
    expected_datetime = datetime(2023, 5, 24, 19, 15, 14)
    assert get_capture_datetime(test_img_camera_watch) == expected_datetime
    assert capture_datetimes_are_consistent(test_img_camera_watch)

    shift_capture_datetime_to_target(
        test_img_camera_watch,
        reference_img=test_img_camera_watch,
        target_time=time(21, 3),
    )
    expected_datetime = datetime(2023, 5, 24, 21, 3, 14)
    assert get_capture_datetime(test_img_camera_watch) == expected_datetime
    assert capture_datetimes_are_consistent(test_img_camera_watch)


def test_shift_capture_datetime_to_target_many_at_time(
    test_img_phone, test_img_camera, test_vid_gopro, test_img_camera_watch
):
    # The watch indicates "21:03"
    # The time of the image is 19:15:14
    # This is a time delta of 1h48m46s, rounded to 1h48.

    shift_capture_datetime_to_target(
        [test_img_phone, test_img_camera, test_vid_gopro],
        reference_img=test_img_camera_watch,
        target_time=time(21, 3),
    )

    expected_date_img_phone = datetime(2023, 5, 17, 11, 18, 3)
    expected_date_img_camera = datetime(2019, 12, 17, 13, 51, 24)
    expected_date_vid = datetime(2023, 6, 23, 17, 55, 15)
    assert get_capture_datetime(test_img_phone) == expected_date_img_phone
    assert get_capture_datetime(test_img_camera) == expected_date_img_camera
    assert get_capture_datetime(test_vid_gopro) == expected_date_vid


def test_shift_capture_datetime_to_target_many_at_time_with_day_shift(
    test_img_phone, test_img_camera, test_vid_gopro, test_img_camera_watch
):
    # In this test, we assume the watch indicates 1 day _before_ the
    # photo was taken.
    # The photo datetime has       2023-05-24 19:15:14 as datetime.
    # Let's assume the watch shows 2023-05-23 21:03:xx.

    shift_capture_datetime_to_target(
        [test_img_phone, test_img_camera, test_vid_gopro],
        reference_img=test_img_camera_watch,
        target_time=datetime(2023, 5, 23, 21, 3),
    )

    expected_date_img_phone = datetime(2023, 5, 16, 11, 18, 3)
    expected_date_img_camera = datetime(2019, 12, 16, 13, 51, 24)
    expected_date_vid = datetime(2023, 6, 22, 17, 55, 15)
    assert get_capture_datetime(test_img_phone) == expected_date_img_phone
    assert get_capture_datetime(test_img_camera) == expected_date_img_camera
    assert get_capture_datetime(test_vid_gopro) == expected_date_vid


def test_express_video_datetime_as_utc(test_vid_camera):
    # Setting the scene: checking that the capture datetime is expected.
    dt = get_capture_datetime(test_vid_camera)
    expected_dt = datetime(2023, 6, 2, 22, 35, 12)  # from a previous test.
    assert dt == expected_dt

    # Checking that the "photo" datetime field has the same datetime.
    # "photo" fields usually are more well-behaved (can be expressed with
    # with a timezone, doesn't require to be expressed in UTC).
    metadata = extract_metadata_using_exiftool(test_vid_camera)
    photo_field = PHOTO_DATETIME_FIELDS[0]
    assert metadata[photo_field.name] == photo_field.unparse(expected_dt)

    # Checking that the "video" datetime field is currently the same as
    # "photo" datetime field (at least up to the hour). This theoretically
    # shouldn't be the case! Because "video" datetime fields are expressed in UTC.
    video_field = VIDEO_DATETIME_FIELDS[0]
    photo_dt = photo_field.parse(metadata[photo_field.name])
    video_dt = video_field.parse(metadata[video_field.name])
    assert photo_dt.date() == video_dt.date()
    assert photo_dt.hour == video_dt.hour
    assert photo_dt.minute == video_dt.minute

    # Now, let's express the "video" datetime field in UTC.
    # First, since this video file doesn't have a timezone, the function
    # should not work.
    with pytest.raises(ValueError):
        express_video_datetime_as_utc(test_vid_camera, errors="raise")

    # To circumvent the error, we can set the errors argument to "coerce".
    # The issue is that this will use the operating system's timezone and
    # will lead to a variable result depending on the machine.
    # Instead, we can hard assign a timezone.
    set_timezone(test_vid_camera, timedelta(seconds=7200))

    # Now finally we can express the video datetime in UTC.
    express_video_datetime_as_utc(test_vid_camera, errors="raise")

    # The 'photo' datetime and overall 'capture datetime' should be unchanged.
    dt = get_capture_datetime(test_vid_camera)
    assert dt == expected_dt

    # The 'video' datetime should now be shifted from the 'photo' datetime by
    # 2 hours.
    metadata = extract_metadata_using_exiftool(test_vid_camera)
    photo_dt = photo_field.parse(metadata[photo_field.name])
    video_dt = video_field.parse(metadata[video_field.name])
    assert photo_dt.date() == video_dt.date()
    assert photo_dt.hour == video_dt.hour + 2
    assert photo_dt.minute == video_dt.minute


def test_express_video_datetime_as_utc_vid_gopro(test_vid_gopro):
    dt = get_capture_datetime(test_vid_gopro)
    expected_datetime = datetime(2023, 6, 23, 16, 7, 15)
    assert dt == expected_datetime
    # This video has timezone = GMT+2.
    assert get_timezone(test_vid_gopro) == timezone(timedelta(hours=2))

    metadata = extract_metadata_using_exiftool(test_vid_gopro)

    # We have two types of fields:
    # 1. The fields that are encoded in local time by GoPro. This is typically
    #    "QuickTime:CreateDate" and "QuickTime:ModifyDate".
    # 2. The fields that are encoded in UTC by GoPro. There's only one:
    #    "GoPro:GPSDateTime".
    # Let's first verify that these two datetimes are currently not the same.

    # Local timezone:
    video_field = ExifDateTimeField("QuickTime:ModifyDate")
    assert video_field in VIDEO_DATETIME_FIELDS
    video_dt = video_field.parse(metadata[video_field.name])
    assert video_dt == expected_datetime

    # UTC timezone:
    video_field = ExifDateTimeField(
        "GoPro:GPSDateTime",
        has_timezone_info=False,
        is_utc=True,
        has_millisecond_info=True,
        has_date_info=True,
    )
    assert video_field in VIDEO_DATETIME_FIELDS
    video_dt = video_field.parse(metadata[video_field.name])
    assert datetime_approx_equal(
        video_dt, datetime(2023, 6, 23, 14, 7, 15)
    )  # expressed in UTC.

    # Now using the function to ensure that *everything* is expressed in UTC.
    # This is the behavior expected by Google Photos. Synology has a different behavior
    # that we can't control (it relies on Exiftool's -api QuickTimeUTC option, which itself
    # relies on the timestamp of the host NAS).
    express_video_datetime_as_utc(test_vid_gopro)
    metadata = extract_metadata_using_exiftool(test_vid_gopro)

    # Doing exactly the same checks as previously:
    # Local timezone:
    video_field = ExifDateTimeField("QuickTime:ModifyDate")
    video_dt = video_field.parse(metadata[video_field.name])
    assert video_dt == datetime(
        2023, 6, 23, 14, 7, 15
    )  # Is now expressed in UTC as well.

    # UTC timezone. Should be unchanged.
    video_field = ExifDateTimeField(
        "GoPro:GPSDateTime",
        has_timezone_info=False,
        is_utc=True,
        has_millisecond_info=True,
        has_date_info=True,
    )
    assert video_field in VIDEO_DATETIME_FIELDS
    video_dt = video_field.parse(metadata[video_field.name])
    assert datetime_approx_equal(video_dt, datetime(2023, 6, 23, 14, 7, 15))

    # In the case of GoPro videos, the timezone can always be inferred from the GPS
    # coordinates.
