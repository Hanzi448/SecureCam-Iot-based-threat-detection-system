# services/inference.py

import cv2
import os
import time
import requests
from pathlib import Path
from ml.yolo_wrapper import predict  # ✅ YOLOv8 wrapper
from services.storage import upload_image
from config import Config

# --- Face Recognition Imports ---
from ml.facenet_wrapper import get_embeddings
from services.face_utils import load_all_watchlist_embeddings
from services.matcher import find_best_match
from services.email_alerts import send_alert
from services.email_throttle import can_send

# --- Base directories ---
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
EVENTS_DIR = DATA_DIR / "events"
CROPS_DIR = EVENTS_DIR / "crops"
OUTPUT_DIR = EVENTS_DIR / "annotated"

for folder in [EVENTS_DIR, CROPS_DIR, OUTPUT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------
# ESP32 Hardware Alert
# ---------------------------------------------------
def trigger_hardware_alert(alert_type: str):
    """Sends a trigger to ESP32 hardware via its /alert endpoint."""
    try:
        esp_url = getattr(Config, "ESP32_ALERT_URL", None)
        if not esp_url:
            print("[ESP32] No ESP32_ALERT_URL configured.")
            return

        full_url = f"{esp_url}/alert?alert={alert_type}"
        resp = requests.get(full_url, timeout=3)
        print(f"[ESP32] Hardware alert sent → {full_url} ({resp.status_code})")

    except Exception as e:
        print(f"[ESP32 WARN] Could not send alert: {e}")


# ---------------------------------------------------
# Core Image Processing
# ---------------------------------------------------
def process_image(local_path: str):
    """
    Full detection pipeline:
    - YOLOv8 weapon detection
    - FaceNet criminal identification
    - Suspicious/unknown person detection (only if occluded/masked)
    - Database + Email + Hardware alert triggers
    """
    img = cv2.imread(local_path)
    if img is None:
        return {"error": f"Could not read image {local_path}"}

    # ✅ YOLOv8 prediction
    detections = predict(img)

    weapon_detected = False
    suspicious_detected = False
    crop_paths = []

    # ---- WEAPON DETECTION ----
    for det in detections:
        label = det["label"].lower()
        conf = det["conf"]
        x1, y1, x2, y2 = det["bbox"]
        weapon_detected = True

        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(img, f"{label} {conf:.2f}", (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        crop = img[y1:y2, x1:x2]
        if crop.size > 0:
            crop_name = f"weapon_crop_{int(time.time() * 1000)}.jpg"
            crop_path = str(CROPS_DIR / crop_name)
            cv2.imwrite(crop_path, crop)
            crop_paths.append(crop_path)

    # ---- Save annotated frame ----
    annotated_name = f"annotated_{int(time.time() * 1000)}.jpg"
    annotated_path = str(OUTPUT_DIR / annotated_name)
    cv2.imwrite(annotated_path, img)

    cloud_url = None
    if Config.CLOUDINARY_CLOUD_NAME:
        try:
            cloud_url = upload_image(annotated_path, folder="events/annotated")
        except Exception as e:
            print(f"[WARN] Cloud upload failed: {e}")

    # ---- FACENET RECOGNITION ----
    criminal_detected = False
    criminal_name = None
    match_distance = None

    try:
        ids, names, db_embs = load_all_watchlist_embeddings()
        faces = get_embeddings(img)

        if not faces or len(faces) == 0:
            print("[INFO] No faces detected — skipping face recognition.")
        else:
            face_matched = False
            for face in faces:
                emb = face["embedding"]
                matched, cid, cname, dist = find_best_match(
                    emb, db_embs, ids, names,
                    threshold=getattr(Config, "FACENET_THRESHOLD", 0.40)
                )
                if matched:
                    criminal_detected = True
                    criminal_name = cname
                    match_distance = dist
                    face_matched = True
                    print(f"[FACENET] Criminal match found: {cname} (dist={dist:.3f})")
                    break

            # ---- SUSPICIOUS CHECK: masked/occluded only ----
            if not face_matched:
                try:
                    bbox = face.get("bbox")
                    if bbox:
                        x1, y1, x2, y2 = map(int, bbox)
                        face_img = img[y1:y2, x1:x2]
                    else:
                        face_img = face.get("crop")

                    if face_img is not None and face_img.size > 0:
                        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
                        lower_half = gray[gray.shape[0] // 2:, :]  # bottom half only
                        variance = cv2.Laplacian(lower_half, cv2.CV_64F).var()

                        if variance < 25:
                            suspicious_detected = True
                            print("[SUSPICIOUS] Possibly masked or occluded face detected.")
                        else:
                            print("[INFO] Unknown but clear face — not suspicious.")
                    else:
                        print("[INFO] Unknown face without valid crop — not marked suspicious.")
                except Exception as e:
                    print(f"[SUSPICIOUS CHECK WARN] {e}")

    except Exception as e:
        print(f"[FACENET WARN] {e}")

    # ---------------------------------------------------
    # ALERT LOGIC + HARDWARE TRIGGER
    # ---------------------------------------------------
    result = {
        "weapon_detected": weapon_detected,
        "detections": detections,
        "criminal_detected": criminal_detected,
        "criminal_name": criminal_name,
        "match_distance": match_distance,
        "suspicious_detected": suspicious_detected,
        "annotated_path": annotated_path,
        "crop_paths": crop_paths,
        "cloud_url": cloud_url
    }

    # Decide alert type
    if weapon_detected and criminal_detected:
        alert_type = "weapon_criminal"
        subject = "[ALERT] Weapon + Criminal Detected"
    elif weapon_detected:
        alert_type = "weapon"
        subject = "[ALERT] Weapon Detected"
    elif criminal_detected:
        alert_type = "criminal"
        subject = "[ALERT] Criminal Identified"
    elif suspicious_detected:
        alert_type = "suspicious"
        subject = "[ALERT] Suspicious Individual Detected"
    else:
        alert_type = None
        subject = None

    # Send alerts
    try:
        if alert_type:
            trigger_hardware_alert(alert_type)

            throttle_key = (
                f"criminal:{criminal_name}"
                if Config.EMAIL_COOLDOWN_SCOPE == "per_criminal" and criminal_name
                else "global"
            )

            if can_send(throttle_key):
                send_alert(result, subject=subject)
            else:
                print(f"[EMAIL] Cooldown active for {throttle_key}")
        else:
            print("[INFO] No threat detected — skipping alerts.")
    except Exception as e:
        print(f"[ALERT WARN] {e}")

    # ---------------------------------------------------
    # DATABASE LOGGING
    # ---------------------------------------------------
    try:
        from services.db_ops import log_event

        confidence = None
        weapon_conf = None
        if detections:
            weapon_conf = detections[0].get("conf")
            confidence = detections[0].get("conf", None)

        log_event(
            image_url=cloud_url,
            local_path=annotated_path,
            weapon_detected=weapon_detected,
            weapon_conf=weapon_conf,
            suspicious=suspicious_detected,
            confidence=confidence,
            criminal_detected=criminal_detected,
            criminal_name=criminal_name,
            match_distance=match_distance,
            alert_sent=bool(alert_type)
        )
    except Exception as e:
        print(f"[DB WARN] Could not log event: {e}")

    return result


if __name__ == "__main__":
    test_img = str(BASE_DIR / "data" / "events" / "frame_1.jpg")
    res = process_image(test_img)
    print(res)
