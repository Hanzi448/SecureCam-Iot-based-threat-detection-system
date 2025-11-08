# services/camera_controller.py
import threading
import time
import cv2
import requests
import numpy as np
from config import Config


class ThreadedCamera:
    def _init_(self, src, reconnect_delay=5, freeze_timeout=5):
        self.src = src
        self.reconnect_delay = reconnect_delay
        self.freeze_timeout = freeze_timeout  # seconds before reconnect if no frames
        self.cap = None
        self.frame = None
        self.lock = threading.Lock()
        self.running = True
        self.last_frame_time = 0
        self.last_reconnect_time = 0

        t = threading.Thread(target=self._update, daemon=True)
        t.start()
        print(f"[ThreadedCamera] Started threaded capture for {src}")

    def _open_source(self):
        """Try to open the camera source safely."""
        if self.cap:
            try:
                self.cap.release()
            except:
                pass
        self.cap = cv2.VideoCapture(self.src)
        if self.cap.isOpened():
            print(f"[ThreadedCamera] Source opened: {self.src}")
            return True
        print(f"[ThreadedCamera] Failed to open source, retry in {self.reconnect_delay}s")
        return False

    def _update(self):
        """Continuously capture frames in a background thread."""
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                if not self._open_source():
                    time.sleep(self.reconnect_delay)
                    continue

            ret, frame = self.cap.read()
            if not ret or frame is None:
                print("[ThreadedCamera] ⚠ Frame read failed — reconnecting...")
                self._open_source()
                time.sleep(0.2)
                continue

            # Store latest frame
            with self.lock:
                self.frame = frame
                self.last_frame_time = time.time()

            # Detect freeze (no frames for freeze_timeout)
            if time.time() - self.last_frame_time > self.freeze_timeout:
                print("[ThreadedCamera] ⚠ Stream frozen — reconnecting...")
                self._open_source()
                time.sleep(1)
                continue

            time.sleep(0.01)  # balance CPU load

    def get_frame(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def stop(self):
        """Stop the capture thread."""
        self.running = False
        if self.cap:
            try:
                self.cap.release()
            except:
                pass
        print("[ThreadedCamera] Stopped gracefully.")


# =====================================================
# Camera Controller (Flask Integration)
# =====================================================
class CameraController:
    def _init_(self, src=None):
        if not src:
            src = getattr(Config, "CAMERA_SOURCE", getattr(Config, "ESP32_URL", 0))

        self.src = src
        self._cam = None
        self._thread = None
        self._running = False
        self._lock = threading.Lock()
        self._latest_frame = None
        self._last_post = 0.0

        self.server_url = getattr(Config, "SERVER_URL", "http://127.0.0.1:5000/api/frame")
        self.api_key = getattr(Config, "CAMERA_API_KEY", None)
        self.post_interval = float(getattr(Config, "CAPTURE_POST_INTERVAL", 2.0))
        self._requests_timeout = 8.0

    # -------------------------------
    # Start / Stop
    # -------------------------------
    def start(self):
        if self._running:
            print("[CAM] Already running.")
            return False
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._running = False
        if self._cam:
            self._cam.stop()
        if self._thread:
            self._thread.join(timeout=5.0)
        print("[CAM] Capture stopped.")
        return True

    def is_running(self):
        return bool(self._running)

    # -------------------------------
    # Capture Loop
    # -------------------------------
    def _capture_loop(self):
        try:
            print(f"[CAM] Initializing threaded camera with freeze protection: {self.src}")
            self._cam = ThreadedCamera(self.src, reconnect_delay=5, freeze_timeout=5)
            last_post = 0.0

            while self._running:
                frame = self._cam.get_frame()
                if frame is None:
                    time.sleep(0.05)
                    continue

                # Encode to JPEG
                ret, jpeg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if not ret:
                    continue
                jpg_bytes = jpeg.tobytes()

                # Update frame for stream
                with self._lock:
                    self._latest_frame = jpg_bytes

                # Post every few seconds
                now = time.time()
                if now - last_post >= self.post_interval:
                    try:
                        files = {"file": ("frame.jpg", jpg_bytes, "image/jpeg")}
                        headers = {"X-API-KEY": self.api_key} if self.api_key else {}
                        requests.post(self.server_url, files=files, headers=headers, timeout=self._requests_timeout)
                    except Exception as e:
                        print(f"[CAM WARN] Post failed: {e}")
                    last_post = now

                time.sleep(0.02)

        except Exception as e:
            print(f"[CAM ERROR] Capture loop crashed: {e}")

        finally:
            if self._cam:
                self._cam.stop()
            self._running = False
            print("[CAM] Capture loop ended.")

    # -------------------------------
    # MJPEG Stream Generator
    # -------------------------------
    def get_latest_frame(self):
        with self._lock:
            return self._latest_frame

    def mjpeg_generator(self):
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
            time.sleep(0.02)


# =====================================================
# Initialize Singleton
# =====================================================
try:
    src = getattr(Config, "CAMERA_SOURCE", getattr(Config, "ESP32_URL", 0))
    camera_controller = CameraController(src=src)
    print(f"[INIT] CameraController ready (freeze-protected) — src={src}")
except Exception as e:
    print(f"[INIT ERROR] {e}")
    camera_controller = CameraController(src=0)