from pathlib import Path

from media_organizer.rename import rename


def test_rename_image_phone(test_img_phone):
    new_name = rename(test_img_phone)
    assert new_name == Path("2023-05-17T09:30:03+02:00-Zonza-Huawei_VOG-L09.jpg")
    assert Path(new_name).exists()


def test_rename_when_two_files_have_the_same_datetime():
    assert False
