from pathlib import Path


def handle_file_path_as_singleton_or_list(func):
    def wrapper(obj_or_list, *args, **kwargs):
        if not isinstance(obj_or_list, list):
            obj_or_list = [obj_or_list]

        formatted_paths = []
        for file_path in obj_or_list:
            file_path = Path(file_path)
            if not file_path.exists():
                # ExifTool will raise an error if the file doesn't exist, but this is a more specific error message.
                raise FileNotFoundError(f"File not found: {file_path}")
            formatted_paths.append(file_path)

        result = func(formatted_paths, *args, **kwargs)
        if result is None:
            return None
        if len(result) == 1:
            return result[0]
        return result

    return wrapper
