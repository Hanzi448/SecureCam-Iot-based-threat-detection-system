# services/threaded_camera.py
import cv2
from threading import Thread, Lock

class ThreadedCamera:
    def _init_(self, src):
        self.cap = cv2.VideoCapture(src)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {src}")

        self.frame = None
        self.lock = Lock()
        self.running = True

        # Start background thread
        t = Thread(target=self._update, daemon=True)
        t.start()
        print(f"[ThreadedCamera] Started background capture for {src}")

    def _update(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            with self.lock:
                self.frame = frame

    def get_frame(self):
        """Return latest frame (or None if not yet available)."""
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy()

    def stop(self):
        """Stop camera thread."""
        self.running = False
        self.cap.release()
        print("[ThreadedCamera] Stopped camera.")