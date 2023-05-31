from pathlib import Path

from media_organizer.rename import (
    rename,
    get_rename_plan,
    gps_coords_to_city_name,
)
from media_organizer.timeshift import (
    extract_metadata_using_exiftool,
    GPSCoordinates,
)


def test_get_rename_plan_photo_phone(test_img_phone):
    new_name = get_rename_plan(test_img_phone)
    assert new_name == Path("2023-05-17T09:30:03+02:00-Zonza-Huawei_VOG-L09.jpg")


def test_get_rename_plan_photo_camera(test_img_camera):
    new_name = get_rename_plan(test_img_camera)
    assert new_name == Path("2019-12-17T12:03:24+02:00-Fujifilm_X-T20.jpg")


def test_get_rename_plan_video(test_vid):
    new_name = get_rename_plan(test_vid)
    assert new_name == Path("2022-04-30T09:33:07+03:00-Toliara-GoPro.mp4")


def test_gps_coords_to_city_name_batch(test_img_phone, test_img_camera, test_vid):
    metadatas = extract_metadata_using_exiftool(
        [test_img_phone, test_img_camera, test_vid]
    )
    gps_coords = GPSCoordinates.from_exif_metadata(metadatas)
    city_names = gps_coords_to_city_name(gps_coords)

    assert city_names == ["Zonza", None, "Toliara"]


def test_get_rename_plan_batch(test_img_phone, test_img_camera, test_vid):
    rename_plan = get_rename_plan([test_img_phone, test_img_camera, test_vid])

    assert rename_plan[test_img_phone] == Path(
        "2023-05-17T09:30:03+02:00-Zonza-Huawei_VOG-L09.jpg"
    )
    assert rename_plan[test_img_camera] == Path(
        "2019-12-17T12:03:24+02:00-Fujifilm_X-T20.jpg"
    )
    assert rename_plan[test_vid] == Path("2022-04-30T09:33:07+03:00-Toliara-GoPro.mp4")


def test_get_rename_plan_when_two_files_have_the_same_datetime():
    assert False
