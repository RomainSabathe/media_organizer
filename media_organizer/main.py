from pathlib import Path
from datetime import timedelta, datetime, time

from tqdm import tqdm
from media_organizer.timeshift import (
    set_timezone,
    shift_capture_datetime_to_target,
    shift_capture_datetime,
    express_video_datetime_as_utc,
)
from media_organizer.rename import search_and_rename
from media_organizer.move import dispatch_according_to_datetime


class LogFile:
    def __init__(self, root_dir, flush_frequency=5):
        self.root_dir = Path(root_dir)
        # create the directory if it doesn't exist
        self.root_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        # use the current datetime as the filename
        self.filename = self.root_dir / (now.isoformat() + ".log")

        self.flush_frequency = flush_frequency
        self.write_count = 0

    def __enter__(self):
        # open the file in write mode
        self.file = self.filename.open("w")
        return self

    def write(self, text):
        # add a newline character after each write
        self.file.write(text + "\n")
        self.write_count += 1

        # if the number of writes has reached the flush frequency, flush the buffer and reset the counter
        if self.write_count == self.flush_frequency:
            self.file.flush()
            self.write_count = 0

    def __exit__(self, exc_type, exc_value, traceback):
        # make sure the buffer is flushed before closing the file
        self.file.flush()
        # close the file
        if self.file:
            self.file.close()


def main():
    # with LogFile("logs") as log_file:
    #    for root_dir in [
    #        Path(
    #            "/volume1/master/10-19.memories/photos/CLEAN_but_need_to_check_for_duplicates_elsewhere"
    #        )
    #    ]:
    #        for extension in tqdm(["mov", "mp4", "MOV", "MP4"]):
    #            file_paths = sorted(list(root_dir.glob(f"**/*{extension}")))
    #            for file_path in tqdm(file_paths):
    #                if '@eaDir' in str(file_path):
    #                    continue
    #                log_file.write(f"Processing {file_path}")
    #                try:
    #                    express_video_datetime_as_utc(file_path)
    #                except ValueError:
    #                    log_file.write(f"Failed to express {file_path} as UTC")

    #    return

    with LogFile("logs") as log_file:
        for root_dir in [Path("/volume1/master/10-19.memories/photos/landing")]:
            reference_img = root_dir / "GX019405.MP4"
            reference_time = time(6, 24, 17)

            # for extension in ["jpg", "mov", "mp4"]:
            for extension in ["MP4"]:
                file_paths = sorted(list(root_dir.glob(f"*{extension}")))
                if not file_paths:
                    continue

                log_file.write(
                    "Running 'shift_capture_datetime_to_target' with the following params:"
                )
                log_file.write(f"  {reference_img=}")
                log_file.write(f"  {reference_time=}")
                log_file.write("and on the following list:")
                for file_path in file_paths:
                    log_file.write(f"  {file_path}")
                shift_capture_datetime_to_target(
                    file_paths, reference_img, reference_time
                )

                log_file.write("Running 'set_timezone' with the following params:")
                log_file.write(f"  timezone=timedelta(hours=2)")
                log_file.write(f"  create_backups=False")
                log_file.write(f"and on the following list:")
                for file_path in file_paths:
                    log_file.write(f"  {file_path}")
                set_timezone(file_paths, timedelta(hours=2), create_backups=False)

            log_file.write("Running 'search_and_rename' with the following params:")
            log_file.write(f"  {root_dir=}")
            log_file.write(f"  output_dir={root_dir}")
            log_file.write(f"  create_backups=False")
            log_file.write(f"  recursive=False")
            log_file.write(f"  create_backups=True")
            search_and_rename(
                root_dir,
                output_dir=root_dir,
                create_backups=False,
                recursive=False,
                create_backups=True,
            )

            log_file.write(
                f"Running 'express_video_datetime_as_utc' with the following params:"
            )
            log_file.write(f"  create_backups=False")
            for extension in tqdm(["mov", "mp4", "MOV", "MP4"]):
                file_paths = sorted(list(root_dir.glob(f"**/*{extension}")))
                for file_path in tqdm(file_paths):
                    if "@eaDir" in str(file_path):
                        continue
                    log_file.write(f"Expressing video datetime as UTC for: {file_path}")
                    try:
                        express_video_datetime_as_utc(file_path, create_backups=False)
                    except ValueError:
                        log_file.write(f"Failed to express {file_path} as UTC")

            dispatch_according_to_datetime(
                root_dir,
                output_dir=root_dir.parent / "gopro_dispatched",
                create_backups=False,
            )


if __name__ == "__main__":
    main()
