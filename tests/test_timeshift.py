from datetime import datetime, timezone, timedelta

import pytest

from media_organizer.timeshift import (
    set_timezone,
    get_timezone,
    get_capture_datetime,
    set_capture_datetime,
    shift_capture_datetime,
    remove_gps_info,
    capture_datetimes_are_consistent,
    extract_metadata_using_exiftool,
    _print_all_exif_datetimes,
    _print_all_exif_gps_info,
    gps_coords_to_timezone,
    GPSCoordinates,
    ProtectedExifAttributes,
)


def test_get_capture_datetime_photo_phone(test_img_phone):
    # TODO: add other `test_img_phone` coming from different cameras (1 phone, 1 GoPro, 1 Fuji)
    expected_date = datetime(2023, 5, 17, 9, 30, 3)
    assert get_capture_datetime(test_img_phone) == expected_date
    assert capture_datetimes_are_consistent(test_img_phone)


def test_get_capture_datetime_photo_camera(test_img_camera):
    # TODO: add other `test_img_phone` coming from different cameras (1 phone, 1 GoPro, 1 Fuji)
    expected_date = datetime(2019, 12, 17, 12, 3, 24)
    assert get_capture_datetime(test_img_camera) == expected_date
    assert capture_datetimes_are_consistent(test_img_camera)


def test_get_capture_datetime_video(test_vid):
    # TODO: add other `test_video` coming from different cameras (1 phone, 1 GoPro, 1 Fuji)
    expected_date = datetime(2022, 4, 30, 9, 33, 7)
    assert get_capture_datetime(test_vid) == expected_date
    assert capture_datetimes_are_consistent(test_vid)


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
    expected_date = datetime(2023, 5, 17, 8, 17, 16)
    shift_capture_datetime(test_img_phone, datetime_shift)

    assert get_capture_datetime(test_img_phone) == expected_date
    assert capture_datetimes_are_consistent(test_img_phone)


def test_shift_capture_datetime_photo_camera(test_img_camera):
    # From a previous test, we know that the original date  is 2019-12-17 12:03:24.
    datetime_shift = timedelta(hours=-2, minutes=47, seconds=13)
    expected_date = datetime(2019, 12, 17, 10, 50, 37)

    shift_capture_datetime(test_img_camera, datetime_shift)
    assert get_capture_datetime(test_img_camera) == expected_date
    assert capture_datetimes_are_consistent(test_img_camera)


def test_shift_capture_datetime_photo_phone_positive_shift(test_img_phone):
    # From a previous test, we know that the original date is 2023-05-17 09:30:03.
    datetime_shift = timedelta(hours=3, minutes=-5, seconds=13)
    expected_date = datetime(2023, 5, 17, 12, 25, 16)

    shift_capture_datetime(test_img_phone, datetime_shift)
    assert get_capture_datetime(test_img_phone) == expected_date
    assert capture_datetimes_are_consistent(test_img_phone)


def test_shift_capture_datetime_photo_camera_positive_shift(test_img_camera):
    # From a previous test, we know that the original date  is 2019-12-17 12:03:24.
    datetime_shift = timedelta(hours=3, minutes=-5, seconds=13)
    expected_date = datetime(2019, 12, 17, 14, 58, 37)

    shift_capture_datetime(test_img_camera, datetime_shift)
    assert get_capture_datetime(test_img_camera) == expected_date
    assert capture_datetimes_are_consistent(test_img_camera)


def test_shift_capture_datetime_video(test_vid):
    # From a previous test, we know that original date is 2022-04-30 09:33:07.
    datetime_shift = timedelta(hours=-2, minutes=47, seconds=13)
    expected_date = datetime(2022, 4, 30, 8, 20, 20)

    shift_capture_datetime(test_vid, datetime_shift)
    assert get_capture_datetime(test_vid) == expected_date
    assert capture_datetimes_are_consistent(test_vid)


def test_shift_capture_datetime_video_positive_shift(test_vid):
    # From a previous test, we know that original date is 2022-04-30 09:33:07.
    datetime_shift = timedelta(hours=3, minutes=-5, seconds=13)
    expected_date = datetime(2022, 4, 30, 12, 28, 20)

    shift_capture_datetime(test_vid, datetime_shift)
    assert get_capture_datetime(test_vid) == expected_date
    assert capture_datetimes_are_consistent(test_vid)


def test_shift_capture_datetime_many_at_a_time(
    test_img_phone, test_img_camera, test_vid
):
    # See previous tests for explanation of these dates.
    expected_date_img_phone = datetime(2023, 5, 17, 8, 17, 16)
    expected_date_img_camera = datetime(2019, 12, 17, 10, 50, 37)
    expected_date_vid = datetime(2022, 4, 30, 8, 20, 20)
    datetime_shift = timedelta(hours=-2, minutes=47, seconds=13)

    shift_capture_datetime([test_img_phone, test_img_camera, test_vid], datetime_shift)
    assert get_capture_datetime(test_img_phone) == expected_date_img_phone
    assert get_capture_datetime(test_img_camera) == expected_date_img_camera
    assert get_capture_datetime(test_vid) == expected_date_vid
    assert capture_datetimes_are_consistent(test_img_phone)
    assert capture_datetimes_are_consistent(test_img_camera)
    assert capture_datetimes_are_consistent(test_vid)


def test_shift_capture_datetime_many_at_a_time_positive_shift(
    test_img_phone, test_img_camera, test_vid
):
    # See previous tests for explanation of these dates.
    expected_date_img_phone = datetime(2023, 5, 17, 12, 25, 16)
    expected_date_img_camera = datetime(2019, 12, 17, 14, 58, 37)
    expected_date_vid = datetime(2022, 4, 30, 12, 28, 20)
    datetime_shift = timedelta(hours=3, minutes=-5, seconds=13)

    shift_capture_datetime([test_img_phone, test_img_camera, test_vid], datetime_shift)
    assert get_capture_datetime(test_img_phone) == expected_date_img_phone
    assert get_capture_datetime(test_img_camera) == expected_date_img_camera
    assert get_capture_datetime(test_vid) == expected_date_vid
    assert capture_datetimes_are_consistent(test_img_phone)
    assert capture_datetimes_are_consistent(test_img_camera)
    assert capture_datetimes_are_consistent(test_vid)


def test_get_timezone_img_phone(test_img_phone):
    assert get_timezone(test_img_phone) == timezone(timedelta(seconds=7200))


def test_get_timezone_img_camera(test_img_camera):
    assert get_timezone(test_img_camera) == timezone(timedelta(hours=2))


def test_get_timezone_video(test_vid):
    assert get_timezone(test_vid) == timezone(timedelta(hours=3))


# We test both positive and negative timezone shifts.
@pytest.mark.parametrize("new_timezone", [timedelta(hours=6), timedelta(hours=-8)])
def test_set_timezone_img_phone(test_img_phone, new_timezone):
    expected_date = datetime(2023, 5, 17, 9, 30, 3)
    assert get_capture_datetime(test_img_phone) == expected_date

    set_timezone(test_img_phone, new_timezone)
    # we use based_on_gps=False because presence of GPS information will dominate
    # the estimate of the timezone information. This is how Google Photos work.
    assert get_timezone(test_img_phone, based_on_gps=False) == timezone(new_timezone)
    assert get_capture_datetime(test_img_phone) == expected_date


# We test both positive and negative timezone shifts.
@pytest.mark.parametrize("new_timezone", [timedelta(hours=6), timedelta(hours=-8)])
def test_set_timezone_video(test_vid, new_timezone):
    expected_date = datetime(2022, 4, 30, 9, 33, 7)
    assert get_capture_datetime(test_vid) == expected_date

    set_timezone(test_vid, new_timezone)
    _print_all_exif_datetimes(test_vid)
    # assert get_timezone(test_vid) == timezone(new_timezone)
    # assert get_capture_datetime(test_vid) == expected_date


def test_google_photos(test_img_phone, test_vid):
    assert True
    # # test_img_phone = (
    # #    "C:/Users/RSaba/git/media_organizer/tests/data/tmp/test_img_phone.jpg"
    # # )
    # test_img_phone = test_vid
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


def test_remove_gps_info_video(test_vid):
    # We can't remove GPS info from GoPro videos because it's stored in an
    # embedded field of Exif metadata.
    with pytest.raises(ProtectedExifAttributes):
        remove_gps_info(test_vid)


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
            GPSCoordinates.from_exif_metadata(metadata)
        )


def test_get_timezone_from_gps_coords_vid(test_vid):
    metadata = extract_metadata_using_exiftool(test_vid)
    extracted_timezone = gps_coords_to_timezone(
        GPSCoordinates.from_exif_metadata(metadata)
    )
    expected_timezone = timezone(timedelta(hours=+3))  # Madagascar
    assert extracted_timezone == expected_timezone
