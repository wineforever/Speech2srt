import os

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from app.config import PROJECT_ROOT, SETTINGS


def create_app():
    app = Flask(__name__)
    app.config["UPLOAD_FOLDER"] = SETTINGS.upload_dir
    app.config["OUTPUT_FOLDER"] = SETTINGS.output_dir
    app.config["MAX_CONTENT_LENGTH"] = SETTINGS.max_content_length
    app.config["JSON_AS_ASCII"] = False

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

    CORS(app)

    from app.routes import api

    app.register_blueprint(api, url_prefix="/api")

    frontend_dist = os.getenv("SPEECH2SRT_FRONTEND_DIST") or os.path.join(
        PROJECT_ROOT, "frontend", "dist"
    )
    frontend_dist = os.path.abspath(frontend_dist)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        if path == "api" or path.startswith("api/"):
            return jsonify({"error": "Not found"}), 404

        if os.path.isdir(frontend_dist):
            target = os.path.join(frontend_dist, path)
            if path and os.path.isfile(target):
                return send_from_directory(frontend_dist, path)
            return send_from_directory(frontend_dist, "index.html")

        return jsonify(
            {
                "error": "Frontend dist not found",
                "hint": "Run `npm run build` in the frontend directory first.",
            }
        ), 500

    return app
