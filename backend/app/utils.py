import os
import uuid

from app.config import SETTINGS


def generate_unique_filename(original_filename):
    ext = get_file_extension(original_filename)
    unique_id = uuid.uuid4().hex
    return f"{unique_id}.{ext}" if ext else unique_id


def format_time(seconds):
    total_ms = max(0, int(round(seconds * 1000)))
    hours = total_ms // 3_600_000
    minutes = (total_ms % 3_600_000) // 60_000
    secs = (total_ms % 60_000) // 1000
    ms = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def is_supported_format(filename):
    ext = get_file_extension(filename)
    return ext in SETTINGS.supported_formats


def get_file_extension(filename):
    return filename.rsplit(".", 1)[1].lower() if "." in filename else ""


def cleanup_files(file_paths):
    for file_path in file_paths:
        if not file_path:
            continue
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
