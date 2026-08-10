"""Command-line interface for Speech2SRT."""

import argparse
import sys

from .application import transcribe_file
from .asr_engines import ENGINE_IDS
from .asr_service import release_model
from .config import DEFAULT_CONFIG_PATH, SETTINGS, reload_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="speech2srt",
        description="Transcribe an audio file to SRT and TXT subtitles.",
    )
    parser.add_argument("input", help="Input audio file")
    parser.add_argument(
        "-o", "--output-dir", default=None,
        help="Output directory (default: configured output directory)",
    )
    parser.add_argument(
        "--asr-engine", default=None, metavar="ENGINE",
        help=f"ASR engine: {', '.join(ENGINE_IDS)} (default: configured engine)",
    )
    parser.add_argument("--language", default=None, help="Optional ASR language")
    parser.add_argument(
        "--config", default=DEFAULT_CONFIG_PATH,
        help=f"Path to INI config file (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--subtitle-max-chars", type=_positive_int, default=None,
        help="Maximum characters per subtitle sentence",
    )
    parser.add_argument(
        "--subtitle-min-duration", type=_non_negative_float, default=None,
        help="Minimum subtitle duration per segment in seconds",
    )
    return parser


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def _non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be 0 or greater")
    return parsed


def _progress(progress: int, message: str) -> None:
    print(f"[{progress:>3}%] {message}", flush=True)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    overrides = {
        key: value
        for key, value in {
            "output_dir": args.output_dir,
            "asr_engine": args.asr_engine,
            "subtitle_max_chars": args.subtitle_max_chars,
            "subtitle_min_duration": args.subtitle_min_duration,
        }.items()
        if value is not None
    }
    try:
        reload_settings(config_path=args.config, overrides=overrides)
        result = transcribe_file(
            args.input,
            language=args.language,
            asr_engine=args.asr_engine,
            progress_cb=_progress,
        )
        print(f"Audio: {result.duration_seconds:.2f}s")
        print(f"SRT: {result.srt_path}")
        print(f"TXT: {result.txt_path}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2 if isinstance(exc, FileNotFoundError) else 1
    finally:
        if SETTINGS.asr_unload_after_task:
            release_model()
