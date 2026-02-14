import os
import re
import uuid

from app.config import SETTINGS


def generate_unique_filename(original_filename):
    ext = get_file_extension(original_filename)
    unique_id = uuid.uuid4().hex
    return f"{unique_id}.{ext}" if ext else unique_id


def get_filename_stem(filename):
    base_name = os.path.basename(str(filename or ""))
    return os.path.splitext(base_name)[0]


def sanitize_filename_part(name, fallback="audio"):
    value = str(name or "").strip()
    value = re.sub(r'[\\/:*?"<>|]+', "_", value)
    value = value.replace(" ", "_")
    value = re.sub(r"_+", "_", value)
    value = value.strip("._")
    return value or fallback


def build_output_filename(source_filename, version_name="", fallback_ext="wav"):
    source_stem = sanitize_filename_part(get_filename_stem(source_filename), fallback="audio")
    version_part = sanitize_filename_part(version_name, fallback="") if version_name else ""
    ext = get_file_extension(source_filename) or str(fallback_ext).lower() or "wav"
    ext = sanitize_filename_part(ext, fallback="wav").lower()

    if version_part:
        base_name = f"{source_stem}_{version_part}"
    else:
        base_name = source_stem
    return f"{base_name}.{ext}"


def ensure_unique_filename(directory, filename):
    base_name, ext = os.path.splitext(filename)
    candidate = filename
    index = 1
    while os.path.exists(os.path.join(directory, candidate)):
        candidate = f"{base_name}_{index}{ext}"
        index += 1
    return candidate


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
