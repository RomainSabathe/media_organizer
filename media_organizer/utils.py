from pathlib import Path


from pathlib import Path


def handle_single_or_list(is_file_path=False):
    def actual_decorator(func):
        def wrapper(obj_or_list, *args, **kwargs):
            if not isinstance(obj_or_list, list):
                obj_or_list = [obj_or_list]

            if is_file_path:
                obj_or_list = [Path(p) for p in obj_or_list]
                for file_path in obj_or_list:
                    if not file_path.exists():
                        # ExifTool will raise an error if the file doesn't exist, but this is a more specific error message.
                        raise FileNotFoundError(f"File not found: {file_path}")

            result = func(obj_or_list, *args, **kwargs)
            if result is None:
                return None
            if len(result) == 1:
                return result[0]
            return result

        return wrapper

    return actual_decorator
