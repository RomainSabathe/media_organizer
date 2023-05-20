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


def test_set_capture_datetime_multiple_at_a_time(test_media_files):
    old_dates = [get_capture_datetime(f) for f in test_media_files]
    new_date = datetime(2023, 5, 20, 15, 20, 0)
    assert all([old_date != new_date for old_date in old_dates])

    set_capture_datetime(test_media_files, new_date)
    assert all([get_capture_datetime(f) == new_date for f in test_media_files])
    assert all([capture_datetimes_are_consistent(f) for f in test_media_files])


def test_shift_capture_datetime_photo(test_img):
    # From a previous test, we know that the original date is 2023-05-17 09:30:03.
    new_date = timedelta(hours=-1, minutes=47, seconds=0)
    expected_date = datetime(2023, 5, 17, 9, 17, 3)

    shift_capture_datetime(test_img, new_date)
    assert get_capture_datetime(test_img) == expected_date
    assert capture_datetimes_are_consistent(test_img)


def test_shift_capture_datetime_video(test_vid):
    # From a previous test, we know that original date is 2022-04-30 09:33:07.
    new_date = timedelta(hours=-1, minutes=47, seconds=0)
    expected_date = datetime(2022, 4, 30, 9, 20, 7)

    shift_capture_datetime(test_vid, new_date)
    assert get_capture_datetime(test_vid) == expected_date
    assert capture_datetimes_are_consistent(test_vid)


def test_determine_timezone(test_img):
    # TODO: add the same test for a video.
    assert determine_timezone(test_img) == timezone(
        timedelta(seconds=7201, microseconds=975657)
    )
