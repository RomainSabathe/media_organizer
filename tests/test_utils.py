from pathlib import Path

import pytest

from media_organizer.utils import handle_single_or_list


def test_handle_single_or_list():
    @handle_single_or_list()
    def dummy_function(objs):
        return [obj + 1 for obj in objs]

    # Sending a singleton should return a singleton
    assert dummy_function(1) == 2

    # Sending a list should return a list
    assert dummy_function([1, 2]) == [2, 3]


def test_handle_file_path_as_singleton_or_list_returns_none(
    test_img_phone, test_img_camera
):
    @handle_single_or_list
    def dummy_function(file_paths):
        return None

    assert dummy_function(test_img_phone) is None
    assert dummy_function([test_img_phone, test_img_camera]) is None


def test_handle_file_paths_being_singleton_or_list(test_img_phone, test_img_camera):
    @handle_single_or_list(is_file_path=True)
    def dummy_function(file_paths):
        return [file_paths.name for file_paths in file_paths]

    # Sending a singleton should return a singleton
    assert dummy_function(test_img_phone) == test_img_phone.name

    # Sending a list should return a list
    assert dummy_function([test_img_phone, test_img_camera]) == [
        test_img_phone.name,
        test_img_camera.name,
    ]

    # Sending a singleton that doesn't exist should raise an error
    with pytest.raises(FileNotFoundError):
        dummy_function(Path("non_existent_file.jpg"))

    # Sending a list with a file that doesn't exist should raise an error
    with pytest.raises(FileNotFoundError):
        dummy_function([test_img_phone, Path("non_existent_file.jpg")])


def test_handle_file_path_as_singleton_or_list_returns_none(
    test_img_phone, test_img_camera
):
    @handle_single_or_list()
    def dummy_function(file_paths):
        return None

    assert dummy_function(test_img_phone) is None
    assert dummy_function([test_img_phone, test_img_camera]) is None
