from datetime import datetime, timezone, timedelta

from media_organizer.timeshift import (
    get_capture_datetime,
    set_capture_datetime,
    shift_capture_datetime,
    capture_datetimes_are_consistent,
    determine_timezone,
    _print_all_exif_datetimes,
)


def test_get_capture_datetime_photo(test_img):
    # TODO: add other `test_img` coming from different cameras (1 phone, 1 GoPro, 1 Fuji)
    expected_date = datetime(2023, 5, 17, 9, 30, 3)
    assert get_capture_datetime(test_img) == expected_date
    assert capture_datetimes_are_consistent(test_img)


def test_get_capture_datetime_video(test_vid):
    # TODO: add other `test_video` coming from different cameras (1 phone, 1 GoPro, 1 Fuji)
    expected_date = datetime(2022, 4, 30, 9, 33, 7)
    assert get_capture_datetime(test_vid) == expected_date
    assert capture_datetimes_are_consistent(test_vid)


def test_set_capture_datetime_one_at_a_time(test_media_file):
    old_date = get_capture_datetime(test_media_file)
    new_date = datetime(2023, 5, 20, 15, 20, 0)
    assert old_date != new_date

    set_capture_datetime(test_media_file, new_date)
    assert get_capture_datetime(test_media_file) == new_date
    assert capture_datetimes_are_consistent(test_media_file)


def test_set_capture_datetime_many_at_a_time(test_media_files):
    old_dates = [get_capture_datetime(f) for f in test_media_files]
    new_date = datetime(2023, 5, 20, 15, 20, 0)
    assert all([old_date != new_date for old_date in old_dates])

    set_capture_datetime(test_media_files, new_date)
    assert all([get_capture_datetime(f) == new_date for f in test_media_files])
    assert all([capture_datetimes_are_consistent(f) for f in test_media_files])


def test_shift_capture_datetime_photo(test_img):
    # From a previous test, we know that the original date is 2023-05-17 09:30:03.
    datetime_shift = timedelta(hours=-2, minutes=47, seconds=13)
    expected_date = datetime(2023, 5, 17, 8, 17, 16)

    shift_capture_datetime(test_img, datetime_shift)
    assert get_capture_datetime(test_img) == expected_date
    assert capture_datetimes_are_consistent(test_img)


def test_shift_capture_datetime_video(test_vid):
    # From a previous test, we know that original date is 2022-04-30 09:33:07.
    datetime_shift = timedelta(hours=-2, minutes=47, seconds=13)
    expected_date = datetime(2022, 4, 30, 8, 20, 20)

    shift_capture_datetime(test_vid, datetime_shift)
    assert get_capture_datetime(test_vid) == expected_date
    assert capture_datetimes_are_consistent(test_vid)


def test_shift_capture_datetime_many_at_a_time(test_img, test_vid):
    # See previous tests for explanation of these dates.
    expected_date_img = datetime(2023, 5, 17, 8, 17, 16)
    expected_date_vid = datetime(2022, 4, 30, 8, 20, 20)
    datetime_shift = timedelta(hours=-2, minutes=47, seconds=13)

    shift_capture_datetime([test_img, test_vid], datetime_shift)
    assert get_capture_datetime(test_img) == expected_date_img
    assert get_capture_datetime(test_vid) == expected_date_vid
    assert capture_datetimes_are_consistent(test_img)
    assert capture_datetimes_are_consistent(test_vid)


def test_determine_timezone_img(test_img):
    assert determine_timezone(test_img) == timezone(
        timedelta(seconds=7201, microseconds=975657)
    )


def test_determine_timezone_video(test_vid):
    # GoPro videos don't provide datetime fields with timezone info.
    assert determine_timezone(test_vid) is None
