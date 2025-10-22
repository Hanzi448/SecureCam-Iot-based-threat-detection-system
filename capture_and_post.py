# capture_and_post.py
import cv2
import requests
import os
from config import Config

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:5000/api/frame")
API_KEY = Config.CAMERA_API_KEY

def capture_frame_and_post():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open webcam")
        return
    cv2.imshow("Captured", frame)
    cv2.waitKey(1000)  # shows for 1 second
    cv2.destroyAllWindows()
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Failed to capture frame")
        return

    # encode as JPEG in-memory
    ret, buf = cv2.imencode('.jpg', frame)
    if not ret:
        print("Failed to encode frame")
        return

    files = {'image': ('frame.jpg', buf.tobytes(), 'image/jpeg')}
    headers = {'X-API-KEY': API_KEY}
    print(f"Posting to {SERVER_URL} ...")
    resp = requests.post(SERVER_URL, files=files, headers=headers, timeout=10)
    try:
        print("Response:", resp.status_code, resp.json())
    except Exception:
        print("Response text:", resp.text)

if __name__ == "__main__":
    capture_frame_and_post()
