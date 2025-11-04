# services/inference.py

import cv2
import os
import time
import requests
from pathlib import Path
from ml.yolo_wrapper import predict
from services.storage import upload_image
from config import Config

# --- NEW imports for FaceNet ---
from ml.facenet_wrapper import get_embeddings
from services.face_utils import load_all_watchlist_embeddings
from services.matcher import find_best_match
from services.email_alerts import send_alert
from services.email_throttle import can_send


# Base directories
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
EVENTS_DIR = DATA_DIR / "events"
CROPS_DIR = EVENTS_DIR / "crops"
OUTPUT_DIR = EVENTS_DIR / "annotated"

# Ensure folders exist
for folder in [EVENTS_DIR, CROPS_DIR, OUTPUT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


def trigger_hardware_alert(alert_type: str):
    """
    Sends a trigger to ESP32 / hardware module.
    You can set ESP32_ALERT_URL in config to define where to send signal.
    """
    try:
        esp_url = getattr(Config, "ESP32_ALERT_URL", None)
        if not esp_url:
            return

        requests.get(f"{esp_url}?alert={alert_type}", timeout=3)
        print(f"[ESP32] Hardware alert triggered: {alert_type}")
    except Exception as e:
        print(f"[ESP32 WARN] Failed to contact ESP32: {e}")


def process_image(local_path: str):
    """
    Processes an image:
    - Runs YOLO weapon detection
    - Runs FaceNet for criminal recognition
    - Detects suspicious (masked/unknown faces)
    - Logs results, emails, and triggers hardware alerts
    """
    img = cv2.imread(local_path)
    if img is None:
        return {"error": f"Could not read image {local_path}"}

    detections = predict(img, conf_thresh=Config.WEAPON_CONF_THRESHOLD)

    weapon_detected = False
    suspicious_detected = False
    crop_paths = []
    annotated_path = None

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

    # Save annotated image
    annotated_name = f"annotated_{int(time.time() * 1000)}.jpg"
    annotated_path = str(OUTPUT_DIR / annotated_name)
    cv2.imwrite(annotated_path, img)

    # Upload annotated image
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
    suspicious_detected = False

    try:
        ids, names, db_embs = load_all_watchlist_embeddings()
        faces = get_embeddings(img)

        if not faces or len(faces) == 0:
            # ✅ Do NOT mark as suspicious if no face at all
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
                    face_matched = True
                    criminal_detected = True
                    criminal_name = cname
                    match_distance = dist
                    print(f"[FACENET] Criminal match found: {cname} (dist={dist:.3f})")
                    break

            if not face_matched:
                # suspicious only if face detected but unmatched
                suspicious_detected = True
                print("[SUSPICIOUS] Face found but not matched in watchlist (unknown/covered).")

    except Exception as e:
        print(f"[FACENET WARN] {e}")

    # ---- ALERT LOGIC (refined priority tree) ----
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

    # Choose cooldown key
    if Config.EMAIL_COOLDOWN_SCOPE == "global":
        throttle_key = "global"
    elif Config.EMAIL_COOLDOWN_SCOPE == "per_criminal" and criminal_detected and criminal_name:
        throttle_key = f"criminal:{criminal_name}"
    else:
        throttle_key = "global"

    try:
        # Determine which alert to send
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
            subject = "[ALERT] Suspicious Individual Detected (Mask / Concealment)"
        else:
            alert_type = None

        alert_needed = alert_type is not None

        if alert_needed:
            if can_send(throttle_key):
                send_alert(result, subject=subject)
                trigger_hardware_alert(alert_type)
            else:
                print(f"[EMAIL] Cooldown active (key={throttle_key})")
        else:
            print("[INFO] No threat detected — skipping email.")

    except Exception as e:
        print(f"[EMAIL WARN] {e}")

    # ---- DATABASE LOGGING ----
    try:
        from services.db_ops import log_event

        confidence = None
        weapon_conf = None
        if detections:
            weapon_conf = detections[0].get("conf")
            confidence = detections[0].get("conf", None)

        image_url = cloud_url
        local = annotated_path

        log_event(
            image_url=image_url,
            local_path=local,
            weapon_detected=weapon_detected,
            weapon_conf=weapon_conf,
            suspicious=suspicious_detected,
            confidence=confidence,
            criminal_detected=criminal_detected,
            criminal_name=criminal_name,
            match_distance=match_distance,
            alert_sent=alert_needed
        )
    except Exception as e:
        print(f"[DB WARN] Could not log event: {e}")

    return result


if __name__ == "__main__":
    test_img = str(BASE_DIR / "data" / "events" / "frame_1.jpg")
    res = process_image(test_img)
    print(res)
