# services/camera_controller.py
import threading
import time
import cv2
import requests
from concurrent.futures import ThreadPoolExecutor
from config import Config
from services.threaded_camera import ThreadedCamera

class CameraController:
    """
    ESP32-first CameraController.
    Posting to backend is asynchronous so capture never blocks.
    """

    def __init__(self, src=None):
        # Always default to CAMERA_SOURCE or ESP32_URL, but start() will always use ESP.
        self.src = src or getattr(Config, "CAMERA_SOURCE", getattr(Config, "ESP32_URL", 0))
        self._cam = None
        self._thread = None
        self._running = False
        self._lock = threading.Lock()
        self._latest_frame = None

        # post settings
        self.server_url = getattr(Config, "SERVER_URL", "http://127.0.0.1:5000/api/frame")
        self.api_key = getattr(Config, "CAMERA_API_KEY", None)
        self.post_interval = float(getattr(Config, "CAPTURE_POST_INTERVAL", 2.0))
        self._requests_timeout = float(getattr(Config, "CAPTURE_REQUESTS_TIMEOUT", 12.0))

        # freeze / reconnect tuning
        self.reconnect_delay = float(getattr(Config, "CAPTURE_RECONNECT_DELAY", 2.0))
        self.freeze_timeout = float(getattr(Config, "CAPTURE_FREEZE_TIMEOUT", 8.0))

        # threadpool for non-blocking posts
        self._executor = ThreadPoolExecutor(max_workers=2)

    def start(self):
        """
        Start capture using ESP32 URL configured in Config. (Webcam option removed)
        """
        if self._running:
            print("[CAM] Already running.")
            return False

        # Recreate a fresh executor every time you start the camera
        self._executor = ThreadPoolExecutor(max_workers=2)

        self.src = getattr(Config, "ESP32_URL", self.src)
        print(f"[CAM] Starting capture (ESP) -> {self.src}")
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        return True


    def stop(self):
        if not self._running:
            return True
        self._running = False

        # stop threaded camera
        if self._cam:
            try:
                self._cam.stop()
            except Exception:
                pass
            self._cam = None

        # wait thread
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

        # Gracefully shutdown executor
        try:
            self._executor.shutdown(wait=False, cancel_futures=False)
        except Exception as e:
            print(f"[CAM WARN] Executor shutdown error: {e}")

        print("[CAM] Capture stopped.")
        return True


    def is_running(self):
        return bool(self._running)

    def _post_frame(self, jpg_bytes):
        """Do the HTTP POST to backend in separate thread."""
        try:
            files = {"file": ("frame.jpg", jpg_bytes, "image/jpeg")}
            headers = {"X-API-KEY": self.api_key} if self.api_key else {}
            resp = requests.post(self.server_url, files=files, headers=headers, timeout=self._requests_timeout)
            # optional: short log
            # print(f"[CAM POST] {resp.status_code}")
        except Exception as e:
            print(f"[CAM WARN] Post failed: {e}")

    def _capture_loop(self):
        try:
            print(f"[CAM] Initializing threaded camera: {self.src}")
            # requests_timeout passed to ThreadedCamera for requests fallback
            self._cam = ThreadedCamera(self.src, reconnect_delay=self.reconnect_delay, requests_timeout=self._requests_timeout)
            last_post = 0.0
            last_frame_time = time.time()

            while self._running:
                frame = self._cam.get_frame()
                if frame is None:
                    # no frame yet — give camera a moment
                    time.sleep(0.02)
                    continue

                # update last_frame_time when we successfully retrieved a frame
                last_frame_time = time.time()

                # encode jpg
                try:
                    ok, jpeg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                    if not ok:
                        time.sleep(0.01)
                        continue
                    jpg_bytes = jpeg.tobytes()
                except Exception as e:
                    print(f"[CAM ERROR] Encoding failed: {e}")
                    time.sleep(0.02)
                    continue

                # store for MJPEG streaming
                with self._lock:
                    self._latest_frame = jpg_bytes

                # Post asynchronously at configured interval
                now = time.time()
                if now - last_post >= self.post_interval:
                    # submit non-blocking post
                    try:
                        self._executor.submit(self._post_frame, jpg_bytes)
                    except Exception as e:
                        print(f"[CAM WARN] Failed to submit post task: {e}")
                    last_post = now

                # freeze detection: if no new frame for freeze_timeout seconds, reconnect
                if time.time() - last_frame_time > self.freeze_timeout:
                    print("[CAM] ⚠ Stream frozen — reconnecting...")
                    try:
                        self._cam.stop()
                    except Exception:
                        pass
                    time.sleep(self.reconnect_delay)
                    self._cam = ThreadedCamera(self.src, reconnect_delay=self.reconnect_delay, requests_timeout=self._requests_timeout)
                    last_frame_time = time.time()

                time.sleep(0.01)

        except Exception as e:
            print(f"[CAM ERROR] Capture loop crashed: {e}")

        finally:
            try:
                if self._cam:
                    self._cam.stop()
            except Exception:
                pass
            self._running = False
            print("[CAM] Capture loop ended.")

    # streaming support
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


# singleton init
try:
    default_src = getattr(Config, "CAMERA_SOURCE", getattr(Config, "ESP32_URL", 0))
    camera_controller = CameraController(src=default_src)
    print(f"[INIT] CameraController initialized — default src={default_src}")
except Exception as e:
    print(f"[INIT ERROR] {e}")
    camera_controller = CameraController(src=0)
