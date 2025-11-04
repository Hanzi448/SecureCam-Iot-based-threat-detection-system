# services/camera_controller.py
import threading
import time
import cv2
import requests
import numpy as np
from config import Config


class CameraController:
    """
    Handles live camera capture from ESP32 or webcam,
    posts frames to backend, and provides MJPEG streaming for Flask.
    """

    def __init__(self, src=None):
        # Prefer config-defined source
        if not src:
            src = getattr(Config, "CAMERA_SOURCE", 0)

        self.src = src
        self._cap = None
        self._thread = None
        self._running = False
        self._lock = threading.Lock()
        self._latest_frame = None  # bytes (JPEG)
        self._last_post = 0.0

        # Backend server settings
        self.server_url = getattr(Config, "SERVER_URL", "http://127.0.0.1:5000/api/frame")
        self.api_key = getattr(Config, "CAMERA_API_KEY", None)
        self.post_interval = getattr(Config, "CAPTURE_POST_INTERVAL", 2.0)  # seconds

    # --------------------------------------------------------
    # Core control methods
    # --------------------------------------------------------
    def start(self):
        """Start background capture loop."""
        if self._running:
            print("[CAM] Already running.")
            return False
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """Stop capture gracefully."""
        if not self._running:
            return False
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        self._thread = None
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        print("[CAM] Capture stopped.")
        return True

    def is_running(self):
        return bool(self._running)

    # --------------------------------------------------------
    # Capture + posting loop
    # --------------------------------------------------------
    def _capture_loop(self):
        try:
            print(f"[CAM] Initializing source: {self.src}")

            # -------------------------------
            # ESP32 (HTTP MJPEG stream) MODE
            # -------------------------------
            if isinstance(self.src, str) and self.src.startswith("http"):
                print("[CAM] Detected ESP32 HTTP stream.")
                while self._running:
                    try:
                        r = requests.get(self.src, timeout=5)
                        if r.status_code != 200:
                            print(f"[ESP32 WARN] HTTP {r.status_code}")
                            time.sleep(1)
                            continue

                        img_array = np.frombuffer(r.content, np.uint8)
                        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        if frame is None:
                            print("[ESP32 ERROR] Could not decode frame")
                            continue

                        # Encode to JPEG (re-encode for consistency)
                        ret2, jpeg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                        if not ret2:
                            continue
                        jpg_bytes = jpeg.tobytes()

                        with self._lock:
                            self._latest_frame = jpg_bytes

                        now = time.time()
                        if now - self._last_post >= self.post_interval:
                            try:
                                files = {"file": ("frame.jpg", jpg_bytes, "image/jpeg")}
                                headers = {"X-API-KEY": self.api_key} if self.api_key else {}
                                resp = requests.post(self.server_url, files=files, headers=headers, timeout=6)
                                print(f"[ESP32 POST] {resp.status_code}")
                            except Exception as e:
                                print(f"[ESP32 WARN] Post failed: {e}")
                            self._last_post = now

                        time.sleep(0.03)

                    except Exception as e:
                        print(f"[ESP32 ERROR] {e}")
                        time.sleep(1)

            # -------------------------------
            # WEBCAM MODE
            # -------------------------------
            else:
                print("[CAM] Using local webcam.")
                cap = cv2.VideoCapture(int(self.src))
                if not cap.isOpened():
                    print(f"[CAM ERROR] Could not open webcam: {self.src}")
                    self._running = False
                    return

                self._cap = cap
                while self._running:
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        print("[CAM WARN] No frame received.")
                        time.sleep(0.2)
                        continue

                    ret2, jpeg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                    if not ret2:
                        continue
                    jpg_bytes = jpeg.tobytes()

                    with self._lock:
                        self._latest_frame = jpg_bytes

                    now = time.time()
                    if now - self._last_post >= self.post_interval:
                        try:
                            files = {"file": ("frame.jpg", jpg_bytes, "image/jpeg")}
                            headers = {"X-API-KEY": self.api_key} if self.api_key else {}
                            requests.post(self.server_url, files=files, headers=headers, timeout=6)
                            print("[CAM POST] Frame sent.")
                        except Exception as e:
                            print(f"[CAM WARN] Post failed: {e}")
                        self._last_post = now

                    time.sleep(0.03)

        except Exception as e:
            print(f"[CAM ERROR] Capture loop crashed: {e}")

        finally:
            try:
                if self._cap:
                    self._cap.release()
            except Exception:
                pass
            self._cap = None
            self._running = False
            print("[CAM] Capture loop ended.")

    # --------------------------------------------------------
    # Stream + latest frame access
    # --------------------------------------------------------
    def get_latest_frame(self):
        """Return latest JPEG bytes (or None if empty)."""
        with self._lock:
            return self._latest_frame

    def mjpeg_generator(self):
        """Flask Response generator for MJPEG streaming."""
        boundary = b"--frame\r\n"
        while True:
            if not self._running:
                time.sleep(0.2)
                continue
            frame = self.get_latest_frame()
            if frame is None:
                time.sleep(0.05)
                continue
            yield boundary
            yield b"Content-Type: image/jpeg\r\n"
            yield b"Content-Length: " + str(len(frame)).encode() + b"\r\n\r\n"
            yield frame
            yield b"\r\n"
            time.sleep(0.03)


# --------------------------------------------------------
# ✅ Initialize camera controller (Auto ESP32 / Webcam)
# --------------------------------------------------------
try:
    src = getattr(Config, "CAMERA_SOURCE", getattr(Config, "ESP32_URL", 0))
    if isinstance(src, str) and src.startswith("http"):
        print(f"[INIT] Using ESP32 stream: {src}")
    else:
        print("[INIT] Using local webcam source.")
    camera_controller = CameraController(src=src)
except Exception as e:
    print(f"[INIT ERROR] {e}")
    camera_controller = CameraController(src=0)
