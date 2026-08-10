import argparse
import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.asr_engines import resolve_asr_engine
from app.asr_service import release_model, transcribe_audio_chunked
from app.audio_processor import validate_audio
from app.config import DEFAULT_CONFIG_PATH, SETTINGS, reload_settings
from app.subtitle_generator import generate_subtitles


def build_parser():
    parser = argparse.ArgumentParser(
        description="Transcribe an audio file to SRT and TXT subtitles."
    )
    parser.add_argument("input", help="Input audio file")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="Output directory (default: configured output directory)",
    )
    parser.add_argument(
        "--asr-engine",
        default=None,
        help="ASR engine (default: bcut)",
    )
    parser.add_argument("--language", default=None, help="Optional ASR language")
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to INI config file (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--subtitle-max-chars",
        type=int,
        default=None,
        help="Maximum characters per subtitle sentence",
    )
    parser.add_argument(
        "--subtitle-min-duration",
        type=float,
        default=None,
        help="Minimum subtitle duration per segment in seconds",
    )
    return parser


def _progress(progress, message):
    print(f"[{progress:>3}%] {message}", flush=True)


def main(argv=None):
    args = build_parser().parse_args(argv)
    input_path = os.path.abspath(args.input)
    if not os.path.isfile(input_path):
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 2

    overrides = {}
    if args.output_dir is not None:
        overrides["output_dir"] = args.output_dir
    if args.asr_engine is not None:
        overrides["asr_engine"] = args.asr_engine
    if args.subtitle_max_chars is not None:
        overrides["subtitle_max_chars"] = args.subtitle_max_chars
    if args.subtitle_min_duration is not None:
        overrides["subtitle_min_duration"] = args.subtitle_min_duration
    reload_settings(config_path=args.config, overrides=overrides)

    try:
        engine = resolve_asr_engine(args.asr_engine, fallback=SETTINGS.asr_engine)
        os.makedirs(SETTINGS.output_dir, exist_ok=True)
        _progress(5, "Validating audio")
        duration = validate_audio(input_path)
        _progress(10, f"Transcribing with {engine} (original audio, no cropping)")
        result = transcribe_audio_chunked(
            input_path,
            language=args.language,
            asr_engine=engine,
            progress_cb=_progress,
        )
        _progress(90, "Generating SRT and TXT")
        subtitle_result = generate_subtitles(
            result,
            SETTINGS.output_dir,
            os.path.basename(input_path),
            output_formats={"srt": True, "txt": True},
        )
        _progress(100, "Completed")
        print(f"Audio: {duration:.2f}s")
        print(f"SRT: {subtitle_result['srt']}")
        print(f"TXT: {subtitle_result['txt']}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        if SETTINGS.asr_unload_after_task:
            release_model()


if __name__ == "__main__":
    raise SystemExit(main())
