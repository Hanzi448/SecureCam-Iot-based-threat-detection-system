import cv2
import os
import time
from pathlib import Path
from ml.yolo_wrapper import predict
from services.storage import upload_image  # Cloudinary upload
from config import Config

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
    - Loads it
    - Runs YOLO weapon detection
    - Saves cropped weapons + annotated image
    - Returns detection summary
    """

    # Load image
    img = cv2.imread(local_path)
    if img is None:
        return {"error": f"Could not read image {local_path}"}

    detections = predict(img, conf_thresh=Config.WEAPON_CONF_THRESHOLD)

    weapon_detected = False
    crop_paths = []
    annotated_path = None

    # Draw boxes and save crops
    for det in detections:
        label = det["label"].lower()
        conf = det["conf"]
        x1, y1, x2, y2 = det["bbox"]

        # Mark as weapon (our model only detects weapons)
        weapon_detected = True

        # Draw box
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(img, f"{label} {conf:.2f}", (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Save crop for evidence
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
            cloud_url = None
            print(f"[WARN] Cloud upload failed: {e}")

    return {
        "weapon_detected": weapon_detected,
        "detections": detections,
        "annotated_path": annotated_path,
        "crop_paths": crop_paths,
        "cloud_url": cloud_url
    }

# For quick manual testing
if __name__ == "__main__":
    test_img = str(BASE_DIR / "data" / "events" / "frame_1.jpg")
    result = process_image(test_img)
    print(result)
