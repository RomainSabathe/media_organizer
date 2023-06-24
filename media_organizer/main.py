from pathlib import Path
from datetime import timedelta

from media_organizer.timeshift import (
    shift_capture_datetime_to_target,
    shift_capture_datetime,
)
from media_organizer.rename import search_and_rename


def main():
    root_dir = Path("C:/Users/RSaba/Pictures/20230422")
    file_paths = list(root_dir.glob("*mp4"))
    if len(file_paths) == 0:
        print(f"No files found at {root_dir}")
        return
    shift_capture_datetime(file_paths, timedelta(minutes=-30))
    search_and_rename(
        root_dir,
        output_dir=root_dir / "renamed",
        create_backups=False,
        recursive=False,
    )


if __name__ == "__main__":
    main()
