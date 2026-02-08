import os
from dataclasses import dataclass

def _env(key, default=None):
    value = os.getenv(key)
    return value if value is not None else default

def _env_bool(key, default=False):
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

def _env_int(key, default=0):
    value = os.getenv(key)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default

def _env_float(key, default=0.0):
    value = os.getenv(key)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir))

DEFAULT_MODEL_PATH = r"F:\\Models\\Qwen\\Qwen3-ASR-0.6B"

@dataclass(frozen=True)
class Settings:
    upload_dir: str = os.path.join(PROJECT_ROOT, "uploads")
    output_dir: str = os.path.join(PROJECT_ROOT, "outputs")
    max_content_length: int = _env_int("MAX_CONTENT_LENGTH_MB", 100) * 1024 * 1024

    supported_formats: tuple = tuple(
        ext.strip().lower() for ext in _env("SUPPORTED_FORMATS", "wav,mp3").split(",")
    )
    max_audio_duration: float = _env_float("MAX_AUDIO_DURATION", 0)

    task_max_concurrent: int = _env_int("MAX_CONCURRENT_TASKS", 3)

    asr_model_path: str = _env("ASR_MODEL_PATH", DEFAULT_MODEL_PATH)
    asr_device: str = _env("ASR_DEVICE", "cuda:0")
    asr_dtype: str = _env("ASR_DTYPE", "bfloat16")
    asr_local_files_only: bool = _env_bool("ASR_LOCAL_FILES_ONLY", True)
    asr_attn_implementation: str = _env("ASR_ATTENTION_IMPL", "")
    asr_max_batch_size: int = _env_int("ASR_MAX_BATCH_SIZE", 32)
    asr_max_new_tokens: int = _env_int("ASR_MAX_NEW_TOKENS", 2048)
    asr_chunk_seconds: float = _env_float("ASR_CHUNK_SECONDS", 60)
    asr_unload_after_task: bool = _env_bool("ASR_UNLOAD_AFTER_TASK", True)
    asr_trust_remote_code: bool = _env_bool("ASR_TRUST_REMOTE_CODE", True)

    subtitle_max_chars: int = _env_int("SUBTITLE_MAX_CHARS", 60)
    subtitle_min_duration: float = _env_float("SUBTITLE_MIN_DURATION", 0.4)
    preview_max_chars: int = _env_int("PREVIEW_MAX_CHARS", 8000)
    preview_max_segments: int = _env_int("PREVIEW_MAX_SEGMENTS", 200)

SETTINGS = Settings()
