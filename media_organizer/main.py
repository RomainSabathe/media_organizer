from pathlib import Path
from datetime import timedelta, datetime

from tqdm import tqdm
from media_organizer.timeshift import (
    shift_capture_datetime_to_target,
    shift_capture_datetime,
    express_video_datetime_as_utc,
)
from media_organizer.rename import search_and_rename

class LogFile:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        # create the directory if it doesn't exist
        self.root_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        # use the current datetime as the filename
        self.filename = self.root_dir / (now.isoformat() + '.log')

    def __enter__(self):
        # open the file in write mode
        self.file = self.filename.open('w')
        return self

    def write(self, text):
        # add a newline character after each write
        self.file.write(text + '\n')

    def __exit__(self, exc_type, exc_value, traceback):
        # close the file
        if self.file:
            self.file.close()



def main():
    with LogFile("logs") as log_file:
        for root_dir in [
            Path(
                "/volume1/master/10-19.memories/photos/CLEAN_but_need_to_check_for_duplicates_elsewhere"
            )
        ]:
            for extension in tqdm(["mov", "mp4", "MOV", "MP4"]):
                file_paths = sorted(list(root_dir.glob(f"**/*{extension}")))
                for file_path in tqdm(file_paths):
                    if '@eaDir' in str(file_path):
                        continue
                    log_file.write(f"Processing {file_path}")
                    try:
                        express_video_datetime_as_utc(file_path)
                    except ValueError:
                        log_file.write(f"Failed to express {file_path} as UTC")

        return


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
