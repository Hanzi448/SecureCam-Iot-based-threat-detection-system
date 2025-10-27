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

    print("Press 'q' to quit, capturing every 2 seconds...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame")
            break

        # Optional: show preview
        cv2.imshow("Smart Surveillance - Press Q to Stop", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Encode as JPEG
        ret, buf = cv2.imencode('.jpg', frame)
        if not ret:
            print("Failed to encode frame")
            continue

        files = {'file': ('frame.jpg', buf.tobytes(), 'image/jpeg')}
        headers = {'X-API-KEY': API_KEY}
        print(f"Posting frame to {SERVER_URL} ...")

        try:
            resp = requests.post(SERVER_URL, files=files, headers=headers, timeout=10)
            print("Response:", resp.status_code, resp.json())
        except Exception as e:
            print(f"[HTTP WARN] {e}")

        # capture frame every few seconds
        cv2.waitKey(2000)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    capture_frame_and_post()
