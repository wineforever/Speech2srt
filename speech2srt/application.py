"""Application-level orchestration for one transcription job."""

from dataclasses import dataclass
import os
from typing import Callable, Optional

from .asr_engines import ENGINE_QWEN3_LOCAL, resolve_asr_engine
from .asr_service import transcribe_audio_chunked
from .audio_processor import validate_audio
from .config import SETTINGS
from .subtitle_generator import generate_subtitles

ProgressCallback = Callable[[int, str], None]


@dataclass(frozen=True)
class TranscriptionResult:
    """Paths and metadata produced by a completed transcription."""

    input_path: str
    engine: str
    duration_seconds: float
    srt_path: str
    txt_path: str


def transcribe_file(
    input_path: str,
    *,
    language: Optional[str] = None,
    asr_engine: Optional[str] = None,
    progress_cb: Optional[ProgressCallback] = None,
) -> TranscriptionResult:
    """Validate, transcribe and render one audio file.

    Configuration is loaded before this function is called. This boundary is
    intentionally independent from argparse, so other Python callers can reuse
    the workflow without invoking the CLI.
    """

    resolved_input = os.path.abspath(input_path)
    if not os.path.isfile(resolved_input):
        raise FileNotFoundError(f"Input file not found: {resolved_input}")

    engine = resolve_asr_engine(asr_engine, fallback=SETTINGS.asr_engine)
    os.makedirs(SETTINGS.output_dir, exist_ok=True)

    _report(progress_cb, 5, "Validating audio")
    duration = validate_audio(resolved_input)
    audio_mode = (
        "local chunking when needed"
        if engine == ENGINE_QWEN3_LOCAL
        else "original audio, no cropping"
    )
    _report(progress_cb, 10, f"Transcribing with {engine} ({audio_mode})")
    asr_result = transcribe_audio_chunked(
        resolved_input,
        language=language,
        asr_engine=engine,
        progress_cb=progress_cb,
    )
    _report(progress_cb, 90, "Generating SRT and TXT")
    outputs = generate_subtitles(
        asr_result,
        SETTINGS.output_dir,
        os.path.basename(resolved_input),
        output_formats={"srt": True, "txt": True},
    )
    _report(progress_cb, 100, "Completed")

    return TranscriptionResult(
        input_path=resolved_input,
        engine=engine,
        duration_seconds=duration,
        srt_path=outputs["srt"],
        txt_path=outputs["txt"],
    )


def _report(callback: Optional[ProgressCallback], progress: int, message: str) -> None:
    if callback:
        callback(progress, message)
