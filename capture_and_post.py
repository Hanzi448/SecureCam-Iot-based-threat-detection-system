# capture_and_post.py
import cv2
import requests
import os
import numpy as np
from config import Config

ESP32_URL = getattr(Config, "ESP32_URL", os.getenv("ESP32_URL", "http://192.168.137.144"))
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:5000/api/frame")
API_KEY = getattr(Config, "CAMERA_API_KEY", None)

def capture_frame_and_post():
    src = ESP32_URL
    print(f"[INFO] Opening ESP32 source: {src}")
    cap = cv2.VideoCapture(src)

    if not cap.isOpened():
        print(f"[ERROR] Could not open source: {src}")
        return

    print(f"[INFO] Posting frames to {SERVER_URL} (press 'q' to quit)")

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("[WARN] No frame received — retrying...")
            cv2.waitKey(100)
            continue

        cv2.imshow("SecureCam (ESP)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            continue

        files = {'file': ('frame.jpg', buf.tobytes(), 'image/jpeg')}
        headers = {'X-API-KEY': API_KEY} if API_KEY else {}
        try:
            resp = requests.post(SERVER_URL, files=files, headers=headers, timeout=10)
            print(f"[POST] {resp.status_code}")
        except Exception as e:
            print(f"[HTTP WARN] {e}")
            cv2.waitKey(2000)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_frame_and_post()
