import argparse
import os

from app.config import DEFAULT_CONFIG_PATH, reload_settings


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")


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


def parse_args():
    parser = argparse.ArgumentParser(description="speech2srt backend service")
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to INI config file (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument("--host", default=None, help="Flask host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=None, help="Flask port (default: 5000)")
    parser.add_argument("--debug", type=_parse_bool, default=None, help="Enable Flask debug mode")

    parser.add_argument("--upload-dir", dest="upload_dir", default=None, help="Upload directory")
    parser.add_argument("--output-dir", dest="output_dir", default=None, help="Output directory")
    parser.add_argument(
        "--max-concurrent-tasks",
        dest="max_concurrent_tasks",
        type=int,
        default=None,
        help="Maximum concurrent processing tasks",
    )
    parser.add_argument(
        "--max-content-length-mb",
        dest="max_content_length_mb",
        type=int,
        default=None,
        help="Upload size limit in MB",
    )
    parser.add_argument(
        "--supported-formats",
        dest="supported_formats",
        default=None,
        help="Comma-separated list, e.g. wav,mp3",
    )

    parser.add_argument(
        "--asr-engine",
        dest="asr_engine",
        default=None,
        help="ASR engine id, e.g. qwen3_local/bcut/jianying/kuaishou",
    )
    parser.add_argument(
        "--asr-model-path",
        dest="asr_model_path",
        default=None,
        help="Local model path",
    )
    parser.add_argument("--asr-device", dest="asr_device", default=None, help="ASR device")
    parser.add_argument("--asr-dtype", dest="asr_dtype", default=None, help="ASR dtype")
    parser.add_argument(
        "--asr-local-files-only",
        dest="asr_local_files_only",
        type=_parse_bool,
        default=None,
        help="Only load model from local path",
    )
    parser.add_argument(
        "--asr-attention-impl",
        dest="asr_attention_impl",
        default=None,
        help="ASR attention implementation",
    )
    parser.add_argument(
        "--asr-max-batch-size",
        dest="asr_max_batch_size",
        type=int,
        default=None,
        help="ASR max batch size",
    )
    parser.add_argument(
        "--asr-max-new-tokens",
        dest="asr_max_new_tokens",
        type=int,
        default=None,
        help="ASR max new tokens",
    )
    parser.add_argument(
        "--asr-chunk-seconds",
        dest="asr_chunk_seconds",
        type=float,
        default=None,
        help="Audio chunk length in seconds",
    )
    parser.add_argument(
        "--asr-unload-after-task",
        dest="asr_unload_after_task",
        type=_parse_bool,
        default=None,
        help="Unload model after task done",
    )

    parser.add_argument(
        "--subtitle-max-chars",
        dest="subtitle_max_chars",
        type=int,
        default=None,
        help="Subtitle max chars per segment",
    )
    parser.add_argument(
        "--subtitle-min-duration",
        dest="subtitle_min_duration",
        type=float,
        default=None,
        help="Subtitle min duration per segment",
    )

    parser.add_argument(
        "--output-version-name",
        "--version-name",
        dest="output_version_name",
        default=None,
        help="Output filename version suffix, e.g. v1",
    )

    return parser.parse_args()


def build_overrides(args):
    keys = [
        "upload_dir",
        "output_dir",
        "max_concurrent_tasks",
        "max_content_length_mb",
        "supported_formats",
        "asr_engine",
        "asr_model_path",
        "asr_device",
        "asr_dtype",
        "asr_local_files_only",
        "asr_attention_impl",
        "asr_max_batch_size",
        "asr_max_new_tokens",
        "asr_chunk_seconds",
        "asr_unload_after_task",
        "subtitle_max_chars",
        "subtitle_min_duration",
        "output_version_name",
    ]
    overrides = {}
    for key in keys:
        value = getattr(args, key, None)
        if value is not None:
            overrides[key] = value
    return overrides


if __name__ == "__main__":
    args = parse_args()
    overrides = build_overrides(args)
    reload_settings(config_path=args.config, overrides=overrides)

    from app import create_app

    debug = args.debug if args.debug is not None else _env_bool("FLASK_DEBUG", False)
    host = args.host or os.getenv("HOST", "0.0.0.0")
    port = args.port if args.port is not None else _env_int("PORT", 5000)
    app = create_app()
    app.run(debug=debug, host=host, port=port)
