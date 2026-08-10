from pydub import AudioSegment
import os

from .config import SETTINGS
from .utils import get_file_extension, is_supported_format


def load_audio(file_path):
    try:
        return AudioSegment.from_file(file_path)
    except Exception as exc:
        raise Exception(f"Failed to load audio: {exc}") from exc


def audio_duration_seconds(audio):
    return max(0.0, len(audio) / 1000.0)


def crop_audio(audio, start_seconds):
    start_ms = max(0, int(start_seconds * 1000))
    return audio[start_ms:]


def save_audio(audio, output_path, format_override=None):
    try:
        if format_override:
            audio.export(output_path, format=format_override)
        else:
            audio.export(output_path)
        return output_path
    except Exception as exc:
        raise Exception(f"Failed to save audio: {exc}") from exc


def validate_audio(file_path):
    extension = get_file_extension(file_path)
    if not is_supported_format(file_path):
        raise Exception(f"Unsupported file format: {extension}")

    audio = load_audio(file_path)
    duration = audio_duration_seconds(audio)
    if SETTINGS.max_audio_duration > 0 and duration > SETTINGS.max_audio_duration:
        raise Exception(
            f"Audio duration exceeds limit ({SETTINGS.max_audio_duration} seconds)"
        )
    return duration


def export_chunks(audio, chunk_seconds, output_dir, base_name, format_override="wav"):
    if chunk_seconds <= 0:
        return []

    chunks = []
    chunk_ms = int(chunk_seconds * 1000)
    if chunk_ms <= 0:
        return chunks

    total_ms = len(audio)
    index = 0
    for start_ms in range(0, total_ms, chunk_ms):
        end_ms = min(start_ms + chunk_ms, total_ms)
        chunk_audio = audio[start_ms:end_ms]
        chunk_path = os.path.join(
            output_dir, f"{base_name}_chunk_{index:04d}.{format_override}"
        )
        chunk_audio.export(chunk_path, format=format_override)
        chunks.append((chunk_path, start_ms / 1000.0))
        index += 1
    return chunks
