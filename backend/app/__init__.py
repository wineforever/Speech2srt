from flask import Flask
from flask_cors import CORS
import os

from app.config import SETTINGS

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

    return app

app = create_app()
