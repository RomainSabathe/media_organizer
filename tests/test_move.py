from media_organizer.move import dispatch_according_to_datetime
from media_organizer.rename import rename


def test_dispatch_according_to_datetime(
    test_img_phone, test_img_camera, test_vid, test_vid_camera, another_tmp_path
):
    # Step 1: we rename the files to a format that we can test. That is,
    # using our rename functions. The resulting files will be named like this:
    # 2021-08-01_12-00-00-capture-device.jpg
    # We purposefully omit one of the files to test that it is not moved.
    rename_plan = rename(
        [test_img_phone, test_img_camera, test_vid], create_backups=False
    )

    # Step 2: we move the files to a directory according to their capture datetime.
    # The resulting directory structure will be like this:
    # YYYY/MM/2021-08-01_12-00-00-capture-device.jpg
    dispatch_according_to_datetime(
        [
            rename_plan[test_img_phone],
            rename_plan[test_img_camera],
            rename_plan[test_vid],
        ],
        output_dir=another_tmp_path,
        create_backups=False,
    )

    # Step 3: we check that the files have been moved to the correct directories.
    other_tmp_path = another_tmp_path
    assert (other_tmp_path / "2023" / "05" / rename_plan[test_img_phone].name).exists()
    assert (other_tmp_path / "2019" / "12" / rename_plan[test_img_camera].name).exists()
    assert (other_tmp_path / "2022" / "04" / rename_plan[test_vid].name).exists()

    # Step 4: we check that the file that was not renamed has not been moved.
    assert test_vid_camera.exists()

    # Step 5: we check that the files have been moved and not copied.
    assert not test_img_phone.exists()
    assert not test_img_camera.exists()
    assert not test_vid.exists()


def test_dispatch_according_to_datetime_on_file_that_doesnt_exist(tmp_path):
    dispatch_according_to_datetime(["blabla.jpg"], output_dir=tmp_path)
