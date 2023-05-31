from pathlib import Path

from media_organizer.rename import (
    rename,
    rename_one_file,
    _get_rename_plan,
    gps_coords_to_city_name,
)
from media_organizer.timeshift import (
    extract_metadata_using_exiftool,
    GPSCoordinates,
)


def test_get_rename_plan_photo_phone(test_img_phone):
    new_name = _get_rename_plan(test_img_phone)
    assert new_name == Path("2023-05-17_09-30-03_p0200-Zonza-Huawei_VOG-L09.jpg")


def test_get_rename_plan_photo_camera(test_img_camera):
    new_name = _get_rename_plan(test_img_camera)
    assert new_name == Path("2019-12-17_12-03-24_p0200-Fujifilm_X-T20.jpg")


def test_get_rename_plan_video(test_vid):
    new_name = _get_rename_plan(test_vid)
    assert new_name == Path("2022-04-30_09-33-07_p0300-Toliara-GoPro.mp4")


def test_gps_coords_to_city_name_batch(test_img_phone, test_img_camera, test_vid):
    metadatas = extract_metadata_using_exiftool(
        [test_img_phone, test_img_camera, test_vid]
    )
    gps_coords = GPSCoordinates.from_exif_metadata(metadatas)
    city_names = gps_coords_to_city_name(gps_coords)

    assert city_names == ["Zonza", None, "Toliara"]


def test_get_rename_plan_batch(test_img_phone, test_img_camera, test_vid):
    rename_plan = _get_rename_plan([test_img_phone, test_img_camera, test_vid])

    assert rename_plan[test_img_phone] == Path(
        "2023-05-17_09-30-03_p0200-Zonza-Huawei_VOG-L09.jpg"
    )
    assert rename_plan[test_img_camera] == Path(
        "2019-12-17-12-03-24_p0200-Fujifilm_X-T20.jpg"
    )
    assert rename_plan[test_vid] == Path("2022-04-30-09-33-07_p0300-Toliara-GoPro.mp4")


def test_rename_one_file_no_backup(test_img_phone):
    new_path = test_img_phone.parent / "new_name.jpg"
    rename_one_file(test_img_phone, new_path, create_backup=False)

    assert new_path.exists()
    assert not test_img_phone.exists()
    assert not (Path("new_name.jpg.backup")).exists()


def test_rename_one_file_no_backup_custom_output_dir(test_img_phone, another_tmp_path):
    new_path = another_tmp_path / "new_name.jpg"
    rename_one_file(test_img_phone, new_path, create_backup=False)

    assert new_path.exists()
    assert not test_img_phone.exists()
    assert not (Path("new_name.jpg.backup")).exists()


def test_rename_one_file_with_backup(test_img_phone):
    new_path = test_img_phone.parent / "new_name.jpg"
    rename_one_file(test_img_phone, new_path, create_backup=True)

    assert new_path.exists()
    assert not test_img_phone.exists()
    assert test_img_phone.with_suffix(test_img_phone.suffix + ".backup").exists()


def test_batch_rename_singleton_no_backup_no_output_dir(test_img_phone):
    new_path = rename(test_img_phone, create_backups=False)

    assert new_path.name == "2023-05-17_09-30-03_p0200-Zonza-Huawei_VOG-L09.jpg"
    assert new_path.parent == test_img_phone.parent
    assert new_path.exists()
    assert not test_img_phone.exists()


def test_get_rename_plan_when_two_files_have_the_same_datetime():
    assert False
