# services/threaded_camera.py
import cv2
import requests
import numpy as np
import time
from threading import Thread, Lock

class ThreadedCamera:
    """
    Background capture that supports:
    - cv2.VideoCapture(...) for device/streams
    - requests-based single-JPEG fetch (fallback for ESP32)
    Keeps latest frame in memory and reconnects on failure.
    """

    def __init__(self, src, reconnect_delay=2.0, requests_timeout=6.0):
        self.src = src
        self.reconnect_delay = float(reconnect_delay)
        self.requests_timeout = float(requests_timeout)

        self._mode = None  # 'opencv' or 'requests'
        self.cap = None
        self.frame = None
        self.lock = Lock()
        self.running = True

        # Start capture thread
        t = Thread(target=self._update, daemon=True)
        t.start()

    def _open_opencv(self):
        try:
            cap = cv2.VideoCapture(self.src)
            start = time.time()
            # wait briefly for capture to open
            while not cap.isOpened() and (time.time() - start) < 3.0:
                time.sleep(0.1)
            if cap.isOpened():
                self.cap = cap
                self._mode = 'opencv'
                return True
            try:
                cap.release()
            except Exception:
                pass
            return False
        except Exception:
            return False

    def _update(self):
        """
        Decide best mode and continuously capture frames.
        """
        while self.running:
            # If it's an HTTP URL — try cv2 first (works for many MJPEG streams).
            if isinstance(self.src, str) and self.src.startswith("http"):
                # If no cap or not opencv mode, attempt to open opencv
                if self._mode != 'opencv' and not self._open_opencv():
                    # fallback to requests-based single-JPEG fetch
                    self._mode = 'requests'

                if self._mode == 'opencv' and self.cap:
                    try:
                        ret, frame = self.cap.read()
                        if not ret or frame is None:
                            # opencv failed — switch to requests fallback next loop
                            try:
                                self.cap.release()
                            except Exception:
                                pass
                            self.cap = None
                            self._mode = 'requests'
                            time.sleep(0.1)
                            continue
                    except Exception:
                        # on any exception, switch to requests fallback
                        try:
                            if self.cap:
                                self.cap.release()
                        except Exception:
                            pass
                        self.cap = None
                        self._mode = 'requests'
                        time.sleep(0.2)
                        continue

                if self._mode == 'requests':
                    try:
                        r = requests.get(self.src, timeout=self.requests_timeout)
                        if r.status_code != 200 or not r.content:
                            time.sleep(0.2)
                            continue
                        img_array = np.frombuffer(r.content, np.uint8)
                        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        if frame is None:
                            time.sleep(0.2)
                            continue
                    except Exception:
                        time.sleep(0.5)
                        continue

            else:
                # Local webcam or numeric source (not used by ESP-only flow, but supported)
                if self._mode != 'opencv' or self.cap is None:
                    # try open as integer index
                    try:
                        idx = int(self.src)
                    except Exception:
                        idx = self.src
                    try:
                        cap = cv2.VideoCapture(idx)
                        start = time.time()
                        while not cap.isOpened() and (time.time() - start) < 3.0:
                            time.sleep(0.1)
                        if not cap.isOpened():
                            try:
                                cap.release()
                            except Exception:
                                pass
                            time.sleep(self.reconnect_delay)
                            continue
                        self.cap = cap
                        self._mode = 'opencv'
                    except Exception:
                        time.sleep(self.reconnect_delay)
                        continue

                # read from opencv
                try:
                    ret, frame = self.cap.read()
                    if not ret or frame is None:
                        time.sleep(0.05)
                        continue
                except Exception:
                    try:
                        if self.cap:
                            self.cap.release()
                    except Exception:
                        pass
                    self.cap = None
                    self._mode = None
                    time.sleep(0.2)
                    continue

            # store frame
            with self.lock:
                # store a copy to be safe
                self.frame = frame.copy() if frame is not None else None

            # small throttle
            time.sleep(0.01)

    def get_frame(self):
        """Return a copy of latest frame or None."""
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy()

    def stop(self):
        self.running = False
        try:
            if self.cap:
                self.cap.release()
        except Exception:
            pass
        print("[ThreadedCamera] Stopped camera.")
