# api/camera_routes.py
from flask import Blueprint, jsonify, Response, stream_with_context
from services.camera_controller import camera_controller

bp = Blueprint("camera", __name__, url_prefix="/api/camera")


@bp.route("/start", methods=["POST"])
def start_camera():
    # ESP-only: frontend should call POST /api/camera/start (no source param needed)
    if camera_controller.is_running():
        return jsonify({"status":"running"}), 200
    ok = camera_controller.start()
    if ok:
        return jsonify({"status":"started", "source":"esp"}), 200
    return jsonify({"status":"error", "message":"could not start camera"}), 500


@bp.route("/stop", methods=["POST"])
def stop_camera():
    """Stop any running camera."""
    if not camera_controller.is_running():
        return jsonify({"status": "already_stopped"}), 200

    ok = camera_controller.stop()
    if ok:
        return jsonify({"status": "stopped"}), 200

    return jsonify({"status": "error", "message": "could not stop camera"}), 500


@bp.route("/status", methods=["GET"])
def status():
    """Return camera running state."""
    return jsonify({
        "running": camera_controller.is_running()
    }), 200


@bp.route("/video_feed")
def video_feed():
    """
    MJPEG stream of latest frames.
    Example: <img src="/api/camera/video_feed">
    """
    return Response(
        stream_with_context(camera_controller.mjpeg_generator()),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )
