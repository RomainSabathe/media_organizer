from media_organizer.utils import handle_file_path_as_singleton_or_list


def test_handle_file_path_as_singleton_or_list(test_img_phone, test_img_camera):
    @handle_file_path_as_singleton_or_list
    def dummy_function(file_paths):
        return [file_paths.name for file_paths in file_paths]

    # Sending a singleton should return a singleton
    assert dummy_function(test_img_phone) == test_img_phone.name

    # Sending a list should return a list
    assert dummy_function([test_img_phone, test_img_camera]) == [
        test_img_phone.name,
        test_img_camera.name,
    ]


def test_handle_file_path_as_singleton_or_list_returns_none(
    test_img_phone, test_img_camera
):
    @handle_file_path_as_singleton_or_list
    def dummy_function(file_paths):
        return None

    assert dummy_function(test_img_phone) is None
    assert dummy_function([test_img_phone, test_img_camera]) is None
