# ml/yolo_wrapper.py
import cv2
import numpy as np
from pathlib import Path

# Paths to YOLOv4 model files
BASE_DIR = Path(__file__).resolve().parents[1]
CFG_PATH = str(BASE_DIR / "models" / "yolo" / "yolov4-weapon.cfg")
WEIGHTS_PATH = str(BASE_DIR / "models" / "yolo" / "yolov4-weapon.weights")
NAMES_PATH = str(BASE_DIR / "models" / "yolo" / "obj.names")

# Load class names
with open(NAMES_PATH, "r") as f:
    CLASSES = [line.strip() for line in f.readlines()]

# Load YOLO network using OpenCV DNN
net = cv2.dnn.readNetFromDarknet(CFG_PATH, WEIGHTS_PATH)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

# Determine output layer names
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers().flatten()]

def predict(image, conf_thresh=0.4, nms_thresh=0.3):
    """
    Run YOLOv4 detection on a BGR OpenCV image.
    Returns list of dicts: [{'label': str, 'conf': float, 'bbox': [x1,y1,x2,y2]}]
    """
    height, width = image.shape[:2]
    blob = cv2.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    class_ids, confidences, boxes = [], [], []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > conf_thresh:
                center_x, center_y, w, h = (detection[0:4] * np.array([width, height, width, height])).astype("int")
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, int(w), int(h)])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Non-max suppression to reduce overlapping boxes
    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_thresh, nms_thresh)

    detections = []
    if len(indices) > 0:
        for i in indices.flatten():
            x, y, w, h = boxes[i]
            detections.append({
                "label": CLASSES[class_ids[i]],
                "conf": round(confidences[i], 2),
                "bbox": [x, y, x + w, y + h]
            })

    return detections

# Quick self-test
if __name__ == "__main__":
    import cv2
    img_path = str(BASE_DIR / "data" / "events" / "frame_2.jpg")
    img = cv2.imread(img_path)
    dets = predict(img)
    if len(dets) == 0:
        print("No detections")
    else:
        print(dets)
