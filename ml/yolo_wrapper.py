# ml/yolo_wrapper.py
import cv2
import torch
from ultralytics import YOLO
from pathlib import Path

class YOLOv8Detector:
    def __init__(self, model_path="models/yolo/best.pt", names_path="models/yolo/obj.names", device=None):
        # Load YOLOv8 model
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = YOLO(model_path)
        self.model.to(self.device)

        # Load class names
        self.names = self._load_class_names(names_path)

        # Detection thresholds
        self.conf_thres = 0.4
        self.iou_thres = 0.45

    def _load_class_names(self, path):
        p = Path(path)
        if p.exists():
            return [line.strip() for line in p.read_text().splitlines() if line.strip()]
        return []

    def predict(self, img_bgr):
        """Run YOLOv8 prediction on an OpenCV image (BGR)."""
        results = self.model.predict(
            source=img_bgr,
            conf=self.conf_thres,
            iou=self.iou_thres,
            device=self.device,
            verbose=False
        )

        detections = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf.cpu().numpy())
                cls = int(box.cls.cpu().numpy())
                label = self.names[cls] if cls < len(self.names) else f"class_{cls}"

                detections.append({
                    "label": label,
                    "conf": conf,
                    "bbox": [int(x1), int(y1), int(x2), int(y2)]
                })

        return detections


# Singleton-style global detector
_detector = None

def predict(img):
    """Predict using a globally cached model instance."""
    global _detector
    if _detector is None:
        _detector = YOLOv8Detector()
    return _detector.predict(img)
