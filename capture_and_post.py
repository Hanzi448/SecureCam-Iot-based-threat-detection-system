# capture_and_post.py
import cv2
import requests
import os
import numpy as np
from config import Config

# Read from config
ESP32_URL = getattr(Config, "ESP32_URL", os.getenv("ESP32_URL", "http://192.168.137.144"))
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:5000/api/frame")
API_KEY = Config.CAMERA_API_KEY


def capture_frame_and_post():
    print(f"Connecting to: {ESP32_URL}")
    cap = cv2.VideoCapture(ESP32_URL)

    if not cap.isOpened():
        print("[ERROR] Could not connect to ESP32 stream.")
        return

    print("Press 'Q' to quit streaming.\n")

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("[WARN] No frame received — retrying...")
            continue

        # Display live feed
        cv2.imshow("ESP32 Smart Surveillance", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Encode frame to JPEG
        ret, buf = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        files = {'file': ('frame.jpg', buf.tobytes(), 'image/jpeg')}
        headers = {'X-API-KEY': API_KEY}

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
