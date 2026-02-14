import configparser
import os
from dataclasses import dataclass, fields
from typing import Any, Dict, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_ROOT, os.pardir))
DEFAULT_CONFIG_PATH = os.path.join(PROJECT_ROOT, "speech2srt.ini")
DEFAULT_MODEL_PATH = r"F:\\Models\\Qwen\\Qwen3-ASR-0.6B"


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def _to_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _resolve_path(path_value: Any, base_dir: str) -> Optional[str]:
    if path_value is None:
        return None
    text = str(path_value).strip()
    if not text:
        return None
    if os.path.isabs(text):
        return os.path.normpath(text)
    return os.path.normpath(os.path.join(base_dir, text))


def _load_ini_values(config_path: Optional[str]) -> Tuple[Dict[str, str], str]:
    resolved_path = os.path.abspath(config_path or DEFAULT_CONFIG_PATH)
    if not os.path.exists(resolved_path):
        return {}, resolved_path

    parser = configparser.ConfigParser()
    parser.read(resolved_path, encoding="utf-8")

    values: Dict[str, str] = {}
    for section in parser.sections():
        for key, value in parser.items(section):
            values[key.strip().lower()] = value.strip()
    return values, resolved_path


def _pick_value(
    name: str,
    default: Any,
    ini_values: Dict[str, str],
    overrides: Dict[str, Any],
    env_key: Optional[str] = None,
) -> Any:
    if name in overrides:
        return overrides[name]
    if env_key and env_key in os.environ:
        return os.environ[env_key]
    if name in ini_values:
        return ini_values[name]
    return default


@dataclass
class Settings:
    config_path: str
    upload_dir: str
    output_dir: str
    max_content_length: int

    supported_formats: tuple
    max_audio_duration: float

    task_max_concurrent: int

    asr_engine: str
    asr_model_path: str
    asr_device: str
    asr_dtype: str
    asr_local_files_only: bool
    asr_attn_implementation: str
    asr_max_batch_size: int
    asr_max_new_tokens: int
    asr_chunk_seconds: float
    asr_unload_after_task: bool
    asr_trust_remote_code: bool

    subtitle_max_chars: int
    subtitle_min_duration: float
    preview_max_chars: int
    preview_max_segments: int

    output_version_name: str


def load_settings(
    config_path: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> Settings:
    cli_overrides = overrides or {}
    ini_values, resolved_config_path = _load_ini_values(config_path)
    ini_base_dir = os.path.dirname(resolved_config_path)

    upload_dir = _resolve_path(
        _pick_value(
            "upload_dir",
            os.path.join(BACKEND_ROOT, "uploads"),
            ini_values,
            cli_overrides,
            "UPLOAD_DIR",
        ),
        ini_base_dir,
    ) or os.path.join(BACKEND_ROOT, "uploads")
    output_dir = _resolve_path(
        _pick_value(
            "output_dir",
            os.path.join(BACKEND_ROOT, "outputs"),
            ini_values,
            cli_overrides,
            "OUTPUT_DIR",
        ),
        ini_base_dir,
    ) or os.path.join(BACKEND_ROOT, "outputs")

    max_content_length_mb = _to_int(
        _pick_value("max_content_length_mb", 100, ini_values, cli_overrides, "MAX_CONTENT_LENGTH_MB"),
        100,
    )
    max_content_length = max(0, max_content_length_mb) * 1024 * 1024

    supported_formats_raw = _pick_value(
        "supported_formats",
        "wav,mp3",
        ini_values,
        cli_overrides,
        "SUPPORTED_FORMATS",
    )
    supported_formats = tuple(
        ext.strip().lower()
        for ext in str(supported_formats_raw).split(",")
        if ext.strip()
    ) or ("wav", "mp3")

    max_audio_duration = _to_float(
        _pick_value("max_audio_duration", 0, ini_values, cli_overrides, "MAX_AUDIO_DURATION"),
        0.0,
    )
    task_max_concurrent = _to_int(
        _pick_value("max_concurrent_tasks", 3, ini_values, cli_overrides, "MAX_CONCURRENT_TASKS"),
        3,
    )

    asr_engine = str(
        _pick_value("asr_engine", "bcut", ini_values, cli_overrides, "ASR_ENGINE")
    ).strip()
    asr_model_path = str(
        _pick_value("asr_model_path", DEFAULT_MODEL_PATH, ini_values, cli_overrides, "ASR_MODEL_PATH")
    ).strip() or DEFAULT_MODEL_PATH
    asr_device = str(
        _pick_value("asr_device", "cuda:0", ini_values, cli_overrides, "ASR_DEVICE")
    ).strip()
    asr_dtype = str(
        _pick_value("asr_dtype", "bfloat16", ini_values, cli_overrides, "ASR_DTYPE")
    ).strip()
    asr_local_files_only = _to_bool(
        _pick_value("asr_local_files_only", True, ini_values, cli_overrides, "ASR_LOCAL_FILES_ONLY"),
        True,
    )
    asr_attn_implementation = str(
        _pick_value("asr_attention_impl", "", ini_values, cli_overrides, "ASR_ATTENTION_IMPL")
    ).strip()
    asr_max_batch_size = _to_int(
        _pick_value("asr_max_batch_size", 32, ini_values, cli_overrides, "ASR_MAX_BATCH_SIZE"),
        32,
    )
    asr_max_new_tokens = _to_int(
        _pick_value("asr_max_new_tokens", 2048, ini_values, cli_overrides, "ASR_MAX_NEW_TOKENS"),
        2048,
    )
    asr_chunk_seconds = _to_float(
        _pick_value("asr_chunk_seconds", 60, ini_values, cli_overrides, "ASR_CHUNK_SECONDS"),
        60.0,
    )
    asr_unload_after_task = _to_bool(
        _pick_value("asr_unload_after_task", True, ini_values, cli_overrides, "ASR_UNLOAD_AFTER_TASK"),
        True,
    )
    asr_trust_remote_code = _to_bool(
        _pick_value("asr_trust_remote_code", True, ini_values, cli_overrides, "ASR_TRUST_REMOTE_CODE"),
        True,
    )

    subtitle_max_chars = _to_int(
        _pick_value("subtitle_max_chars", 60, ini_values, cli_overrides, "SUBTITLE_MAX_CHARS"),
        60,
    )
    subtitle_min_duration = _to_float(
        _pick_value("subtitle_min_duration", 0.4, ini_values, cli_overrides, "SUBTITLE_MIN_DURATION"),
        0.4,
    )
    preview_max_chars = _to_int(
        _pick_value("preview_max_chars", 8000, ini_values, cli_overrides, "PREVIEW_MAX_CHARS"),
        8000,
    )
    preview_max_segments = _to_int(
        _pick_value("preview_max_segments", 200, ini_values, cli_overrides, "PREVIEW_MAX_SEGMENTS"),
        200,
    )
    output_version_name = str(
        _pick_value("output_version_name", "v1", ini_values, cli_overrides, "OUTPUT_VERSION_NAME")
    ).strip()

    return Settings(
        config_path=resolved_config_path,
        upload_dir=upload_dir,
        output_dir=output_dir,
        max_content_length=max_content_length,
        supported_formats=supported_formats,
        max_audio_duration=max_audio_duration,
        task_max_concurrent=task_max_concurrent,
        asr_engine=asr_engine,
        asr_model_path=asr_model_path,
        asr_device=asr_device,
        asr_dtype=asr_dtype,
        asr_local_files_only=asr_local_files_only,
        asr_attn_implementation=asr_attn_implementation,
        asr_max_batch_size=asr_max_batch_size,
        asr_max_new_tokens=asr_max_new_tokens,
        asr_chunk_seconds=asr_chunk_seconds,
        asr_unload_after_task=asr_unload_after_task,
        asr_trust_remote_code=asr_trust_remote_code,
        subtitle_max_chars=subtitle_max_chars,
        subtitle_min_duration=subtitle_min_duration,
        preview_max_chars=preview_max_chars,
        preview_max_segments=preview_max_segments,
        output_version_name=output_version_name,
    )


SETTINGS = load_settings()


def reload_settings(
    config_path: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> Settings:
    updated = load_settings(config_path=config_path, overrides=overrides)
    for field in fields(Settings):
        setattr(SETTINGS, field.name, getattr(updated, field.name))
    return SETTINGS
