from datetime import datetime

from media_organizer.timeshift import get_capture_datetime, set_capture_datetime


def test_get_capture_datetime_photo(test_img):
    # TODO: add other `test_img` coming from different cameras (1 phone, 1 GoPro, 1 Fuji)
    known_date = datetime(2023, 5, 17, 9, 30, 3)
    assert get_capture_datetime(test_img) == known_date


def test_get_capture_datetime_video(test_vid):
    # TODO: add other `test_video` coming from different cameras (1 phone, 1 GoPro, 1 Fuji)
    known_date = datetime(2022, 4, 30, 9, 33, 7)
    assert get_capture_datetime(test_vid) == known_date


def test_set_capture_datetime(target_media_file):
    old_date = get_capture_datetime(target_media_file)
    new_date = datetime(2023, 5, 20, 15, 20, 0)
    assert old_date != new_date

    set_capture_datetime(target_media_file, new_date)
    assert get_capture_datetime(target_media_file) == new_date
