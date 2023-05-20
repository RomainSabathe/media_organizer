import shutil
from pathlib import Path

import pytest

# Get the path to the directory containing this file
THIS_DIR = Path(__file__).resolve().parent


@pytest.fixture
def test_img():
    # return THIS_DIR / "data" / "tmp" / "test_img_phone.jpg"
    return THIS_DIR / "data" / "test_img_phone.jpg"


@pytest.fixture
def test_vid():
    return THIS_DIR / "data" / "test_vid_gopro.mp4"


@pytest.fixture
def tmp_path(tmp_path):
    # Allows for easier debugging (just replace tmp_path by whatever you like).
    return Path("C:/Users/RSaba/git/media_organizer/tests/data/tmp")
    return tmp_path


@pytest.fixture
def target_media_files(tmp_path, test_img, test_vid):
    """Provides a copy of the photo or video that needs to be timeshifted.
    The reason we provide a copy is so that we don't modify the original file."""
    to_return = []
    media_files = [test_img, test_vid]
    for media_file in media_files:
        temp_file_path = tmp_path / media_file.name
        shutil.copy2(media_file, temp_file_path)
        to_return.append(temp_file_path)
    return to_return


@pytest.fixture(params=["test_img", "test_vid"])
def target_media_file(request, tmp_path):
    """Provides a copy of the photo or video that needs to be timeshifted.
    The reason we provide a copy is so that we don't modify the original file.
    This fixture differs from `target_media_files` in that it only provides one file at a time.
    """
    original_media_file = request.getfixturevalue(request.param)
    temp_file_path = tmp_path / original_media_file.name
    shutil.copy2(original_media_file, temp_file_path)
    return temp_file_path
