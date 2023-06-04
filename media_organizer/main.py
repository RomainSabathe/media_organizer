from pathlib import Path

from media_organizer.timeshift import shift_capture_datetime_to_target
from media_organizer.rename import search_and_rename


def main():
    root_dir = Path("C:/Users/RSaba/Pictures/20230427")
    search_and_rename(
        root_dir, output_dir=root_dir.parent / "renamed", create_backups=False
    )


if __name__ == "__main__":
    main()
