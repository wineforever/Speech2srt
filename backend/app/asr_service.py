import os
import threading
import inspect
import gc

import torch
from qwen_asr import Qwen3ASRModel

from app.asr_engines import (
    ENGINE_QWEN3_LOCAL,
    list_asr_engines,
    resolve_asr_engine,
    transcribe_with_online_engine,
)
from app.config import SETTINGS
from app.audio_processor import load_audio, audio_duration_seconds, export_chunks

_MODEL = None
_MODEL_LOCK = threading.Lock()


def _resolve_dtype(dtype_name):
    name = (dtype_name or "").strip().lower()
    if name == "float16":
        return torch.float16
    if name == "float32":
        return torch.float32
    if name == "bfloat16":
        return torch.bfloat16
    return torch.bfloat16


def _resolve_device(device):
    if device.startswith("cuda") and not torch.cuda.is_available():
        return "cpu"
    return device


def _model_device(model):
    candidates = [model]
    for attr in ("model", "encoder", "decoder", "asr_model", "net"):
        sub = getattr(model, attr, None)
        if sub is not None:
            candidates.append(sub)
    for candidate in candidates:
        try:
            return next(candidate.parameters()).device
        except Exception:
            continue
    return None


def _move_model_to_device(model, device):
    if hasattr(model, "to"):
        model.to(device)
        return True

    for attr in ("model", "encoder", "decoder", "asr_model", "net"):
        sub = getattr(model, attr, None)
        if sub is None:
            continue
        if hasattr(sub, "to"):
            sub.to(device)
            return True

    if hasattr(model, "device"):
        try:
            model.device = device
            return True
        except Exception:
            return False

    return False


def get_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    model_path = SETTINGS.asr_model_path
    if SETTINGS.asr_local_files_only and not os.path.exists(model_path):
        raise RuntimeError(
            "ASR model path not found. Set ASR_MODEL_PATH to a local folder."
        )

    target_device = _resolve_device(SETTINGS.asr_device)
    kwargs = {
        "dtype": _resolve_dtype(SETTINGS.asr_dtype),
        "device_map": target_device,
        "device": target_device,
        "max_inference_batch_size": SETTINGS.asr_max_batch_size,
        "max_new_tokens": SETTINGS.asr_max_new_tokens,
        "local_files_only": SETTINGS.asr_local_files_only,
        "trust_remote_code": SETTINGS.asr_trust_remote_code,
    }

    if SETTINGS.asr_attn_implementation:
        kwargs["attn_implementation"] = SETTINGS.asr_attn_implementation

    signature = inspect.signature(Qwen3ASRModel.from_pretrained)
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in signature.parameters}

    _MODEL = Qwen3ASRModel.from_pretrained(model_path, **filtered_kwargs)
    actual_device = _model_device(_MODEL)
    if (
        target_device.startswith("cuda")
        and torch.cuda.is_available()
        and (actual_device is None or str(actual_device).startswith("cpu"))
    ):
        try:
            if _move_model_to_device(_MODEL, target_device):
                actual_device = _model_device(_MODEL)
        except Exception as exc:
            print(f"[ASR] Warning: failed to move model to {target_device}: {exc}")

    print(
        f"[ASR] Loaded model from {model_path} on {actual_device or 'unknown'} "
        f"(dtype={SETTINGS.asr_dtype}, device_setting={SETTINGS.asr_device}, "
        f"cuda_available={torch.cuda.is_available()})"
    )
    return _MODEL


def release_model():
    global _MODEL
    with _MODEL_LOCK:
        if _MODEL is None:
            return
        _MODEL = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _normalize_segment(segment):
    if isinstance(segment, dict):
        return {
            "start": float(segment.get("start", 0.0)),
            "end": float(segment.get("end", 0.0)),
            "text": str(segment.get("text", "")),
        }

    return {
        "start": float(getattr(segment, "start", 0.0)),
        "end": float(getattr(segment, "end", 0.0)),
        "text": str(getattr(segment, "text", "")),
    }


def _normalize_result(result):
    if isinstance(result, dict):
        text = result.get("text", "")
        language = result.get("language")
        segments = result.get("segments") or []
    else:
        text = getattr(result, "text", "")
        language = getattr(result, "language", None)
        segments = getattr(result, "segments", []) or []

    normalized_segments = [_normalize_segment(seg) for seg in segments]
    if not text and normalized_segments:
        text = " ".join(seg["text"].strip() for seg in normalized_segments).strip()

    return {
        "text": text,
        "language": language,
        "segments": normalized_segments,
    }


def _fallback_segments(text, duration):
    if not text:
        return []

    chunks = [chunk.strip() for chunk in text.replace("\n", " ").split(" ") if chunk.strip()]
    if not chunks:
        return []

    total = len(chunks)
    if duration <= 0:
        duration = total * 0.4

    per = max(duration / total, 0.3)
    segments = []
    cursor = 0.0
    for word in chunks:
        start = cursor
        end = cursor + per
        segments.append({"start": start, "end": end, "text": word})
        cursor = end
    return segments


def _transcribe_with_qwen(audio_path, language=None):
    model = get_model()

    with _MODEL_LOCK, torch.inference_mode():
        transcribe_kwargs = {"audio": audio_path, "language": language}
        signature = inspect.signature(model.transcribe)
        if "device" in signature.parameters:
            transcribe_kwargs["device"] = _resolve_device(SETTINGS.asr_device)
        if "max_new_tokens" in signature.parameters:
            transcribe_kwargs["max_new_tokens"] = SETTINGS.asr_max_new_tokens
        results = model.transcribe(**transcribe_kwargs)

    if isinstance(results, list):
        if not results:
            return {"text": "", "language": language, "segments": []}
        result = results[0]
    else:
        result = results

    normalized = _normalize_result(result)
    if not normalized["segments"]:
        audio = load_audio(audio_path)
        duration = audio_duration_seconds(audio)
        normalized["segments"] = _fallback_segments(normalized["text"], duration)

    return normalized


def transcribe_audio(audio_path, language=None, asr_engine=None):
    resolved_engine = resolve_asr_engine(asr_engine, fallback=SETTINGS.asr_engine)
    if resolved_engine != ENGINE_QWEN3_LOCAL:
        return transcribe_with_online_engine(
            audio_path=audio_path,
            engine=resolved_engine,
            language=language,
        )
    return _transcribe_with_qwen(audio_path, language=language)


def transcribe_audio_chunked(audio_path, language=None, asr_engine=None, progress_cb=None):
    resolved_engine = resolve_asr_engine(asr_engine, fallback=SETTINGS.asr_engine)
    if resolved_engine != ENGINE_QWEN3_LOCAL:
        if progress_cb:
            progress_cb(60, f"Transcribing audio ({resolved_engine})")
        return transcribe_audio(audio_path, language=language, asr_engine=resolved_engine)

    audio = load_audio(audio_path)
    duration = audio_duration_seconds(audio)
    chunk_seconds = SETTINGS.asr_chunk_seconds
    if not chunk_seconds or duration <= chunk_seconds:
        if progress_cb:
            progress_cb(60, "Transcribing audio")
        return transcribe_audio(audio_path, language=language, asr_engine=resolved_engine)

    temp_dir = os.path.join(SETTINGS.output_dir, "chunks")
    os.makedirs(temp_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    chunk_entries = export_chunks(audio, chunk_seconds, temp_dir, base_name)

    all_segments = []
    all_text = []
    detected_language = None

    total = len(chunk_entries)
    try:
        for idx, (chunk_path, offset) in enumerate(chunk_entries, 1):
            if progress_cb:
                progress_cb(30 + int((idx / total) * 50), f"Transcribing chunk {idx}/{total}")

            chunk_result = transcribe_audio(
                chunk_path,
                language=language,
                asr_engine=resolved_engine,
            )
            if not detected_language:
                detected_language = chunk_result.get("language")

            for segment in chunk_result.get("segments", []):
                all_segments.append(
                    {
                        "start": segment["start"] + offset,
                        "end": segment["end"] + offset,
                        "text": segment["text"],
                    }
                )
            if chunk_result.get("text"):
                all_text.append(chunk_result["text"].strip())
    finally:
        for chunk_path, _ in chunk_entries:
            try:
                os.remove(chunk_path)
            except Exception:
                pass

    return {
        "text": " ".join(all_text).strip(),
        "language": detected_language,
        "segments": all_segments,
    }


def get_asr_engines_payload():
    return list_asr_engines(default_engine=SETTINGS.asr_engine)
