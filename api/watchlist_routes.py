# api/watchlist_routes.py
from flask import Blueprint, request, jsonify
import numpy as np
import cv2
import os
from services.face_utils import save_watchlist_entry
from services.storage import upload_image
from ml.facenet_wrapper import get_embeddings

bp = Blueprint("watchlist", __name__)

DATA_DIR = "data/watchlist/tmp"
os.makedirs(DATA_DIR, exist_ok=True)

@bp.route("/watchlist/add", methods=["POST"])
def add_watchlist():
    """Add a new criminal to the database."""
    name = request.form.get("name")
    if not name:
        return jsonify({"error": "Name is required"}), 400

    files = request.files.getlist("images")
    if not files:
        return jsonify({"error": "No images uploaded"}), 400

    all_embs = []
    for f in files:
        path = os.path.join(DATA_DIR, f.filename)
        f.save(path)
        img = cv2.imread(path)
        faces = get_embeddings(img)
        if not faces:
            continue
        all_embs.append(faces[0]["embedding"])  # take first face per image

    if not all_embs:
        return jsonify({"error": "No valid faces detected"}), 400

    emb = np.mean(all_embs, axis=0)
    emb = emb / np.linalg.norm(emb)

    # Upload first image to Cloudinary
    cloud_url = upload_image(path)

    watchlist_id = save_watchlist_entry(name, cloud_url, emb)
    return jsonify({
        "id": watchlist_id,
        "name": name,
        "status": "added",
        "image_url": cloud_url
    })
