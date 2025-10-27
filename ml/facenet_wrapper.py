# ml/facenet_wrapper.py
import torch
import numpy as np
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image
import cv2

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load models
mtcnn = MTCNN(keep_all=True, device=device)
resnet = InceptionResnetV1(pretrained="vggface2").eval().to(device)

def get_embeddings(frame_bgr):
    """
    Detect faces and return their bounding boxes + FaceNet embeddings.
    :param frame_bgr: numpy BGR image (OpenCV)
    :return: list of dicts with {box, embedding}
    """
    # Convert BGR → RGB for PIL
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(frame_rgb)

    # Detect faces
    boxes, _ = mtcnn.detect(pil_img)
    if boxes is None:
        return []

    faces = []
    for box in boxes:
        x1, y1, x2, y2 = [int(b) for b in box]
        face_crop = frame_rgb[y1:y2, x1:x2]
        if face_crop.size == 0:
            continue

        # Prepare tensor for FaceNet
        face_pil = Image.fromarray(face_crop)
        face_tensor = mtcnn.extract(pil_img, [box], save_path=None)
        if face_tensor is None:
            continue

        # Generate embedding
        with torch.no_grad():
            emb = resnet(face_tensor.to(device)).cpu().numpy().flatten()
            emb = emb / np.linalg.norm(emb)  # Normalize

        faces.append({
            "box": [x1, y1, x2, y2],
            "embedding": emb
        })
    return faces
