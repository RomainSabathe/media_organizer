from datetime import datetime

from media_organizer.timeshift import (
    get_capture_datetime,
)


def test_get_capture_datetime_photo(test_img):
    # TODO: add other `test_img` coming from different cameras (1 phone, 1 GoPro, 1 Fuji)
    known_date = datetime(2023, 5, 17, 9, 30, 3)
    assert get_capture_datetime(str(test_img)) == known_date
