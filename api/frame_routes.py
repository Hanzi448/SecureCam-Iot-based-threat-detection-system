from flask import Blueprint, request, jsonify
import os
import time
from pathlib import Path
from services.inference import process_image
from services.storage import upload_image
from config import Config

bp = Blueprint("frame_api", __name__)

# Base directories
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
EVENTS_DIR = DATA_DIR / "events"
EVENTS_DIR.mkdir(parents=True, exist_ok=True)

@bp.route("/frame", methods=["POST"])
def receive_frame():
    """
    Receives a frame (from laptop cam or ESP32-CAM), saves it locally,
    runs YOLOv4 weapon detection, uploads annotated image, and returns detection result.
    """
    try:
        # Check file in request
        if "file" not in request.files:
            return jsonify({"error": "No file received"}), 400

        file = request.files["file"]

        # Save image locally
        ts = int(time.time() * 1000)
        filename = f"frame_{ts}.jpg"
        local_path = str(EVENTS_DIR / filename)
        file.save(local_path)

        print(f"[INFO] Frame received and saved: {local_path}")

        # --- Run YOLOv4 weapon detection ---
        result = process_image(local_path)

        # Ensure consistent output
        response = {
            "status": "processed",
            "weapon_detected": result.get("weapon_detected", False),
            "detections": result.get("detections", []),
            "annotated_path": result.get("annotated_path"),
            "crop_paths": result.get("crop_paths"),
            "cloud_url": result.get("cloud_url"),
        }

        return jsonify(response), 200

    except Exception as e:
        print(f"[ERROR] /api/frame failed: {e}")
        return jsonify({"error": str(e)}), 500
