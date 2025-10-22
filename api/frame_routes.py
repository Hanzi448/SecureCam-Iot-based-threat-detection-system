# api/frame_routes.py
import os
import time
from flask import Blueprint, request, current_app, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path

from services.storage import upload_image  # we added this earlier (Cloudinary helper)
from config import Config

bp = Blueprint("frame", __name__)

# where to save temp frames
BASE_DIR = Path(__file__).resolve().parents[2]
EVENTS_DIR = BASE_DIR / "data" / "events"
EVENTS_DIR.mkdir(parents=True, exist_ok=True)

def _save_file_storage(file_storage, filename):
    local_path = EVENTS_DIR / filename
    file_storage.save(str(local_path))
    return str(local_path)

@bp.route("/frame", methods=["POST"])
def receive_frame():
    """
    POST /api/frame
    Headers:
      - X-API-KEY: <CAMERA_API_KEY>
    Form-data:
      - image: <file>   (preferred)
    OR
      - raw image bytes as body (content-type: image/jpeg)
    Optional query:
      - rotate=1   # if camera is mounted upside-down (server can handle rotation later)
    Response:
      JSON with local_path and optionally cloud_url
    """
    api_key = request.headers.get("X-API-KEY", "")
    if api_key != Config.CAMERA_API_KEY:
        return jsonify({"error": "invalid api key"}), 401

    # try multipart form file first
    file = None
    if "image" in request.files:
        file = request.files["image"]
    else:
        # try raw bytes
        if request.data:
            # create an in-memory file-like object
            from io import BytesIO
            from werkzeug.datastructures import FileStorage
            file = FileStorage(stream=BytesIO(request.data), filename="frame.jpg", content_type=request.content_type)

    if not file:
        return jsonify({"error": "no image provided"}), 400

    fname = secure_filename(f"frame_{int(time.time()*1000)}.jpg")
    local_path = _save_file_storage(file, fname)

    response = {"status": "saved", "local_path": local_path}

    # If Cloudinary configured, upload and return secure_url
    if Config.CLOUDINARY_CLOUD_NAME and Config.CLOUDINARY_API_KEY and Config.CLOUDINARY_API_SECRET:
        try:
            cloud_url = upload_image(local_path, folder="events")
            response["cloud_url"] = cloud_url
        except Exception as e:
            current_app.logger.error(f"cloud upload failed: {e}")
            response["cloud_upload_error"] = str(e)

    # Here we could enqueue a Celery task like: process_frame.delay(local_path, ...)
    # For now we just return saved info.
    return jsonify(response), 202
