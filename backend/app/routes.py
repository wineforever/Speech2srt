from datetime import datetime, timezone
import os

from flask import Blueprint, current_app, jsonify, request, send_from_directory

from app.asr_engines import AsrEngineError, resolve_asr_engine
from app.audio_processor import crop_audio, load_audio, save_audio, validate_audio
from app.asr_service import get_asr_engines_payload, transcribe_audio_chunked, release_model
from app.config import PROJECT_ROOT, SETTINGS
from app.subtitle_generator import generate_subtitles
from app.tasks import task_manager
from app.utils import (
    build_output_filename,
    ensure_unique_filename,
    generate_unique_filename,
    is_supported_format,
)

api = Blueprint("api", __name__)


def _iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _serialize_job(job):
    if not job:
        return None
    return {
        "id": job["id"],
        "status": job["status"],
        "message": job["message"],
        "progress": job["progress"],
        "created_at": _iso(job["created_at"]),
        "updated_at": _iso(job["updated_at"]),
        "output_files": job.get("output_files", {}),
        "previews": job.get("previews", {}),
        "timeline": job.get("timeline", []),
        "duration": job.get("duration"),
        "error": job.get("error"),
    }


def _read_preview(file_path):
    if not file_path or not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            content = handle.read()
        limit = SETTINGS.preview_max_chars
        if limit and len(content) > limit:
            return {"content": content[:limit], "truncated": True}
        return {"content": content, "truncated": False}
    except Exception:
        return None


def _resolve_completion_sound():
    env_path = os.getenv("SPEECH2SRT_SOUND_FILE")
    candidates = [
        env_path,
        os.path.join(PROJECT_ROOT, "Sound.mp3"),
        os.path.join(os.getcwd(), "Sound.mp3"),
    ]
    for path in candidates:
        if not path:
            continue
        full_path = os.path.abspath(path)
        if os.path.isfile(full_path):
            return full_path
    return None


def process_audio_job(job_id, params, update_job):
    try:
        filename = params["filename"]
        original_filename = params.get("original_filename") or filename
        crop_seconds = float(params.get("crop_seconds", 0))
        output_formats = params.get("output_formats") or {"srt": True, "txt": True}
        language = params.get("language")
        asr_engine = params.get("asr_engine")

        upload_folder = SETTINGS.upload_dir
        output_folder = SETTINGS.output_dir

        input_path = os.path.join(upload_folder, filename)
        if not os.path.exists(input_path):
            raise RuntimeError("Uploaded file not found")

        update_job(job_id, progress=5, message="Loading audio")
        audio = load_audio(input_path)

        if crop_seconds > 0:
            update_job(job_id, progress=12, message="Cropping audio")
            audio = crop_audio(audio, crop_seconds)

        audio_duration = audio.duration_seconds if hasattr(audio, "duration_seconds") else None

        update_job(job_id, progress=18, message="Saving processed audio")
        output_filename = build_output_filename(
            original_filename, version_name=SETTINGS.output_version_name
        )
        output_filename = ensure_unique_filename(output_folder, output_filename)
        output_path = os.path.join(output_folder, output_filename)
        save_audio(audio, output_path)

        update_job(job_id, progress=25, message="Transcribing audio")

        def progress_cb(progress, message):
            update_job(job_id, progress=progress, message=message)

        asr_result = transcribe_audio_chunked(
            output_path,
            language=language,
            asr_engine=asr_engine,
            progress_cb=progress_cb,
        )

        update_job(job_id, progress=85, message="Generating subtitles")
        subtitle_result = generate_subtitles(
            asr_result, output_folder, output_filename, output_formats=output_formats
        )

        output_files = {
            "audio": output_filename,
        }
        if subtitle_result.get("srt"):
            output_files["srt"] = os.path.basename(subtitle_result["srt"])
        if subtitle_result.get("txt"):
            output_files["txt"] = os.path.basename(subtitle_result["txt"])

        previews = {}
        srt_preview = _read_preview(subtitle_result.get("srt"))
        if srt_preview:
            previews["srt"] = srt_preview
        txt_preview = _read_preview(subtitle_result.get("txt"))
        if txt_preview:
            previews["txt"] = txt_preview

        timeline = subtitle_result.get("sentences", []) or []
        limit = SETTINGS.preview_max_segments
        if limit and len(timeline) > limit:
            timeline = timeline[:limit]

        update_job(
            job_id,
            progress=95,
            message="Finalizing",
            output_files=output_files,
            previews=previews,
            timeline=timeline,
            duration=audio_duration,
        )
    finally:
        if SETTINGS.asr_unload_after_task and task_manager.get_running_count() <= 1:
            release_model()


@api.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    if not is_supported_format(file.filename):
        allowed = ", ".join(SETTINGS.supported_formats)
        return jsonify({"error": f"Only {allowed} are supported"}), 400

    filename = generate_unique_filename(file.filename)
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        duration = validate_audio(filepath)
    except Exception as exc:
        try:
            os.remove(filepath)
        except Exception:
            pass
        return jsonify({"error": str(exc)}), 400

    return jsonify(
        {
            "success": True,
            "filename": filename,
            "original_filename": file.filename,
            "duration": duration,
        }
    ), 200


@api.route("/process", methods=["POST"])
def process_audio():
    data = request.get_json(silent=True) or {}
    filename = data.get("filename")
    original_filename = data.get("original_filename")
    crop_seconds_raw = data.get("crop_seconds", 0)
    output_formats = data.get("output_formats") or {"srt": True, "txt": True}
    language = data.get("language")
    asr_engine = data.get("asr_engine")

    if not filename:
        return jsonify({"error": "Missing filename"}), 400

    try:
        crop_seconds = float(crop_seconds_raw)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid crop_seconds"}), 400
    try:
        resolved_asr_engine = resolve_asr_engine(asr_engine, fallback=SETTINGS.asr_engine)
    except AsrEngineError as exc:
        return jsonify({"error": str(exc)}), 400

    input_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(input_path):
        return jsonify({"error": "File not found"}), 404

    job_id = task_manager.submit(
        process_audio_job,
        {
            "filename": filename,
            "original_filename": original_filename,
            "crop_seconds": crop_seconds,
            "output_formats": output_formats,
            "language": language,
            "asr_engine": resolved_asr_engine,
        },
    )

    return jsonify({"job_id": job_id}), 202


@api.route("/asr-engines", methods=["GET"])
def asr_engines():
    return jsonify(get_asr_engines_payload()), 200


@api.route("/assets/completion-sound", methods=["GET"])
def completion_sound():
    sound_path = _resolve_completion_sound()
    if not sound_path:
        return jsonify({"error": "Completion sound not found"}), 404

    directory = os.path.dirname(sound_path)
    filename = os.path.basename(sound_path)
    return send_from_directory(directory, filename)


@api.route("/status/<job_id>", methods=["GET"])
def job_status(job_id):
    job = task_manager.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(_serialize_job(job)), 200


@api.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    filepath = os.path.join(current_app.config["OUTPUT_FOLDER"], filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(current_app.config["OUTPUT_FOLDER"], filename, as_attachment=True)


@api.route("/preview/<filename>", methods=["GET"])
def preview_audio(filename):
    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    output_path = os.path.join(current_app.config["OUTPUT_FOLDER"], filename)

    if os.path.exists(upload_path):
        return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(output_path):
        return send_from_directory(current_app.config["OUTPUT_FOLDER"], filename)

    return jsonify({"error": "File not found"}), 404


@api.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200
