import shutil
from pathlib import Path

import pytest

# Get the path to the directory containing this file
THIS_DIR = Path(__file__).resolve().parent


@pytest.fixture
def test_img(tmp_path):
    file_path = THIS_DIR / "data" / "test_img_phone.jpg"

    # Creating a copy of the file so that we don't modify the original file.
    temp_file_path = tmp_path / file_path.name
    shutil.copy2(file_path, temp_file_path)

    yield temp_file_path


@pytest.fixture
def test_vid(tmp_path):
    file_path = THIS_DIR / "data" / "test_vid_gopro.mp4"

    # Creating a copy of the file so that we don't modify the original file.
    temp_file_path = tmp_path / file_path.name
    shutil.copy2(file_path, temp_file_path)

    yield temp_file_path


@pytest.fixture
def tmp_path(tmp_path):
    # Allows for easier debugging (just replace tmp_path by whatever you like).
    # return Path("C:/Users/RSaba/git/media_organizer/tests/data/tmp")
    return tmp_path


@pytest.fixture
def test_media_files(test_img, test_vid):
    return [test_img, test_vid]


@pytest.fixture(params=["test_img", "test_vid"])
def test_media_file(request):
    """Provides a copy of the photo or video that needs to be timeshifted.
    The reason we provide a copy is so that we don't modify the original file.
    This fixture differs from `target_media_files` in that it only provides one file at a time.
    """
    media_file = request.getfixturevalue(request.param)
    return media_file
