from pathlib import Path
import pytest

# Get the path to the directory containing this file
THIS_DIR = Path(__file__).resolve().parent


@pytest.fixture
def test_img():
    return THIS_DIR / "data" / "test_img.jpg"
