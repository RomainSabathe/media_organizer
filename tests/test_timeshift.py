from datetime import datetime, timezone, timedelta

from media_organizer.timeshift import (
    get_capture_datetime,
    set_capture_datetime,
    capture_datetimes_are_consistent,
    determine_timezone,
)


def test_get_capture_datetime_photo(test_img):
    # TODO: add other `test_img` coming from different cameras (1 phone, 1 GoPro, 1 Fuji)
    known_date = datetime(2023, 5, 17, 9, 30, 3)
    assert get_capture_datetime(test_img) == known_date
    # assert capture_datetimes_are_consistent(test_img)


def test_get_capture_datetime_video(test_vid):
    # TODO: add other `test_video` coming from different cameras (1 phone, 1 GoPro, 1 Fuji)
    known_date = datetime(2022, 4, 30, 9, 33, 7)
    assert get_capture_datetime(test_vid) == known_date
    assert capture_datetimes_are_consistent(test_vid)


def test_set_capture_datetime_one_at_a_time(target_media_file):
    old_date = get_capture_datetime(target_media_file)
    new_date = datetime(2023, 5, 20, 15, 20, 0)
    assert old_date != new_date

    set_capture_datetime(target_media_file, new_date)
    assert get_capture_datetime(target_media_file) == new_date
    assert capture_datetimes_are_consistent(target_media_file)


def test_set_capture_datetime_multiple_at_a_time(target_media_files):
    old_dates = [get_capture_datetime(f) for f in target_media_files]
    new_date = datetime(2023, 5, 20, 15, 20, 0)
    assert all([old_date != new_date for old_date in old_dates])

    set_capture_datetime(target_media_files, new_date)
    assert all([get_capture_datetime(f) == new_date for f in target_media_files])
    assert all([capture_datetimes_are_consistent(f) for f in target_media_files])


def test_determine_timezone(test_img):
    # TODO: add the same test for a video.
    assert determine_timezone(test_img) == timezone(timedelta(hours=2))
