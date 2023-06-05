import shutil
from pathlib import Path
from typing import List


def dispatch_according_to_capture_device():
    # TODO: WIP.
    root_dir = Path(r"C:\Users\RSaba\Pictures\Sorted3\2022\08\edinburgh")
    for file in root_dir.iterdir():
        if "Fujifilm" in file.name:
            dest_dir = root_dir / "fuji"
        else:
            dest_dir = root_dir / "mom"
        dest_dir.mkdir(exist_ok=True, parents=True)
        shutil.move(file, dest_dir / file.name)


def dispatch_according_to_datetime(
    file_paths: List[Path],
    output_dir: Path,
    create_backups: bool = False,
):
    """Move files to directories according to their capture datetime according
    to the following format: output_dir/YYYY/MM/

    Only the files that are named according to a certain format are moved.
    The regex is the following: /^YYYY-MM-DD*/

    Args:
        input_dir (Path): The directory to search for files
        output_dir (Path): The directory to move files to
        create_backups (bool, optional): Whether to create backups of files before
            moving them. Defaults to False.
    """
    for file in file_paths:
        file = Path(file)
        if not file.exists():
            continue
        try:
            year, month, *_ = file.name.split("-")
            if not year.isdigit() or not month.isdigit():
                continue
            if len(year) != 4:
                continue
            if len(month) != 2:
                continue

            dest_dir = output_dir / year / month
            dest_dir.mkdir(exist_ok=True, parents=True)

            if create_backups:
                shutil.copy(file, dest_dir / file.name)
            else:
                shutil.move(file, dest_dir / file.name)

        except ValueError:
            print(f"Could not parse {file.name}. Skipping.")
            continue
