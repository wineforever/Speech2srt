import os

from app.config import SETTINGS
from app.utils import format_time
import re


_SENTENCE_DELIMS = r"[。！？!?；;，,、…]"


def _split_text(text):
    parts = re.split(f"({_SENTENCE_DELIMS})", text)
    sentences = []
    buffer = ""
    for idx, part in enumerate(parts):
        if part is None or part == "":
            continue
        buffer += part
        if re.fullmatch(_SENTENCE_DELIMS, part):
            sentence = buffer.strip()
            if sentence:
                sentences.append(sentence)
            buffer = ""
    if buffer.strip():
        sentences.append(buffer.strip())
    return sentences


def _split_long_sentence(text):
    max_chars = SETTINGS.subtitle_max_chars
    if not max_chars or len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end
    return chunks


def _allocate_times(start_time, end_time, texts):
    if not texts:
        return []
    duration = max(0.0, end_time - start_time)
    weights = [max(len(t.strip()), 1) for t in texts]
    total_weight = sum(weights)
    if duration <= 0:
        duration = SETTINGS.subtitle_min_duration * len(texts)
    durations = [duration * w / total_weight for w in weights]
    min_dur = SETTINGS.subtitle_min_duration
    if min_dur:
        adjusted = [max(d, min_dur) for d in durations]
        if sum(adjusted) <= duration or duration <= 0:
            durations = adjusted
    cursor = start_time
    results = []
    for d in durations:
        end = cursor + d
        results.append((cursor, end))
        cursor = end
    if results:
        results[-1] = (results[-1][0], max(results[-1][1], end_time))
    return results


def split_sentences(segments):
    sentences = []
    for segment in segments:
        segment_text = str(segment.get("text", "")).strip()
        if not segment_text:
            continue
        start_time = float(segment.get("start", 0.0))
        end_time = float(segment.get("end", start_time))

        raw_sentences = _split_text(segment_text)
        final_sentences = []
        for raw in raw_sentences:
            final_sentences.extend(_split_long_sentence(raw))

        time_slices = _allocate_times(start_time, end_time, final_sentences)
        for (start, end), text in zip(time_slices, final_sentences):
            end_value = max(end, start + SETTINGS.subtitle_min_duration)
            sentences.append(
                {
                    "start": start,
                    "end": end_value,
                    "text": text,
                }
            )
    return sentences


def generate_srt(sentences, output_path):
    try:
        with open(output_path, "w", encoding="utf-8") as handle:
            for index, sentence in enumerate(sentences, 1):
                start_time = format_time(sentence["start"])
                end_time = format_time(sentence["end"])
                handle.write(f"{index}\n")
                handle.write(f"{start_time} --> {end_time}\n")
                handle.write(f"{sentence['text']}\n\n")
        return output_path
    except Exception as exc:
        raise Exception(f"Failed to generate SRT: {exc}") from exc


def generate_txt(sentences, output_path):
    try:
        with open(output_path, "w", encoding="utf-8") as handle:
            for sentence in sentences:
                handle.write(f"{sentence['text']}\n")
        return output_path
    except Exception as exc:
        raise Exception(f"Failed to generate TXT: {exc}") from exc


def generate_subtitles(asr_result, output_dir, audio_filename, output_formats=None):
    base_name = os.path.splitext(audio_filename)[0]
    sentences = split_sentences(asr_result.get("segments", []))

    outputs = {"sentences": sentences}
    formats = output_formats or {"srt": True, "txt": True}

    if formats.get("srt"):
        srt_path = os.path.join(output_dir, f"{base_name}.srt")
        outputs["srt"] = generate_srt(sentences, srt_path)
    if formats.get("txt"):
        txt_path = os.path.join(output_dir, f"{base_name}.txt")
        outputs["txt"] = generate_txt(sentences, txt_path)

    return outputs
