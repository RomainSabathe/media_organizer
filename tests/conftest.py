import shutil
from pathlib import Path

import pytest

# Get the path to the directory containing this file
THIS_DIR = Path(__file__).resolve().parent


@pytest.fixture
def test_img():
    return THIS_DIR / "data" / "test_img_phone.jpg"


@pytest.fixture
def test_vid():
    return THIS_DIR / "data" / "test_vid_gopro.mp4"


@pytest.fixture(params=["test_img", "test_vid"])
def target_media_file(request, tmp_path):
    """Provides a copy of the photo or video that needs to be timeshifted.
    The reason we provide a copy is so that we don't modify the original file."""
    original_media_file = request.getfixturevalue(request.param)
    temp_file_path = tmp_path / original_media_file.name
    shutil.copy2(original_media_file, temp_file_path)
    return temp_file_path
