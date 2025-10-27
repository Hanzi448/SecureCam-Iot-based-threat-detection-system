import cv2
import os
import time
from pathlib import Path
from ml.yolo_wrapper import predict
from services.storage import upload_image
from config import Config

# --- NEW imports for FaceNet ---
from ml.facenet_wrapper import get_embeddings
from services.face_utils import load_all_watchlist_embeddings
from services.matcher import find_best_match
from services.email_alerts import send_weapon_alert

# Base directories
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
EVENTS_DIR = DATA_DIR / "events"
CROPS_DIR = EVENTS_DIR / "crops"
OUTPUT_DIR = EVENTS_DIR / "annotated"

# Ensure folders exist
for folder in [EVENTS_DIR, CROPS_DIR, OUTPUT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


def process_image(local_path: str):
    """
    Processes an image:
    - Runs YOLO weapon detection
    - Then runs FaceNet for criminal recognition
    - Saves crops + annotated images
    - Logs results and sends email alerts
    """
    img = cv2.imread(local_path)
    if img is None:
        return {"error": f"Could not read image {local_path}"}

    detections = predict(img, conf_thresh=Config.WEAPON_CONF_THRESHOLD)

    weapon_detected = False
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
            crop_name = f"weapon_crop_{int(time.time()*1000)}.jpg"
            crop_path = str(CROPS_DIR / crop_name)
            cv2.imwrite(crop_path, crop)
            crop_paths.append(crop_path)

    # Save annotated image
    annotated_name = f"annotated_{int(time.time()*1000)}.jpg"
    annotated_path = str(OUTPUT_DIR / annotated_name)
    cv2.imwrite(annotated_path, img)

    # Upload annotated image (optional)
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
        for face in faces:
            emb = face["embedding"]
            matched, cid, cname, dist = find_best_match(
                emb, db_embs, ids, names, threshold=getattr(Config, "FACENET_THRESHOLD", 0.40)
            )
            if matched:
                criminal_detected = True
                criminal_name = cname
                match_distance = dist
                print(f"[FACENET] Criminal match found: {cname} (dist={dist:.3f})")
                break
    except Exception as e:
        print(f"[FACENET WARN] {e}")

    # ---- ALERT LOGIC ----
    from services.email_alerts import send_alert

    result = {
        "weapon_detected": weapon_detected,
        "detections": detections,
        "criminal_detected": criminal_detected,
        "criminal_name": criminal_name,
        "match_distance": match_distance,
        "annotated_path": annotated_path,
        "crop_paths": crop_paths,
        "cloud_url": cloud_url
    }

    try:
        if weapon_detected or criminal_detected:
            send_alert(result)
    except Exception as e:
        print(f"[EMAIL WARN] {e}")

    # ---- DATABASE LOGGING ----
    try:
        from services.db_ops import log_event
        conf = detections[0]["conf"] if detections else 0.0
        log_event(
            weapon_detected=weapon_detected,
            confidence=conf,
            annotated_url=cloud_url,
            local_path=annotated_path,
            alert_sent=(weapon_detected or criminal_detected)
        )
    except Exception as e:
        print(f"[DB WARN] Could not log event: {e}")

    return result


if __name__ == "__main__":
    test_img = str(BASE_DIR / "data" / "events" / "frame_1.jpg")
    res = process_image(test_img)
    print(res)
