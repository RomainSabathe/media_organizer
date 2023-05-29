from pathlib import Path

from media_organizer.rename import rename


def test_rename_photo_phone(test_img_phone):
    new_name = rename(test_img_phone)
    assert new_name == Path("2023-05-17T09:30:03+02:00-Zonza-Huawei_VOG-L09.jpg")
    assert Path(new_name).exists()


def test_rename_photo_camera(test_img_camera):
    new_name = rename(test_img_camera)
    assert new_name == Path("2019-12-17T12:03:24+02:00-Fujifilm_X-T20.jpg")
    assert Path(new_name).exists()


def test_rename_video(test_vid):
    new_name = rename(test_vid)
    assert new_name == Path("2022-04-30T09:33:07+03:00-Toliara-GoPro.mp4")
    assert Path(new_name).exists()


def test_rename_batch(test_img_phone, test_img_camera, test_vid):
    new_name_img_phone, new_name_img_camera, new_name_vid = rename(
        [test_img_phone, test_img_camera, test_vid]
    )

    assert new_name_img_phone == Path(
        "2023-05-17T09:30:03+02:00-Zonza-Huawei_VOG-L09.jpg"
    )
    assert new_name_img_camera == Path("2019-12-17T12:03:24+02:00-Fujifilm_X-T20.jpg")
    assert new_name_vid == Path("2022-04-30T09:33:07+03:00-Toliara-GoPro.mp4")


def test_rename_when_two_files_have_the_same_datetime():
    assert False
