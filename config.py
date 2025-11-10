import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

class Config:
    # ------------------ Flask + Database ------------------
    ENV = os.getenv("FLASK_ENV", "production")
    SECRET_KEY = os.getenv("SECRET_KEY", "change_me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv("REDIS_URL")

    # ------------------ Cloudinary ------------------
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    # ------------------ Email / Alerts ------------------
    GMAIL_USER = os.getenv("GMAIL_USER", "your_email@gmail.com")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "your_app_password")  # app password only
    ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "recipient_email@gmail.com")

    # ------------------ Detection Thresholds ------------------
    WEAPON_CONF_THRESHOLD = float(os.getenv("WEAPON_CONF_THRESHOLD", 0.4))
    FACENET_THRESHOLD = float(os.getenv("FACENET_THRESHOLD", 0.45))
    OCULAR_THRESHOLD = float(os.getenv("OCULAR_THRESHOLD", 0.55))

    # ------------------ YOLOv8 Weapon Model ------------------
    YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "models/new_model/best.onnx")
    YOLO_INPUT_SIZE = int(os.getenv("YOLO_INPUT_SIZE", "640"))
    YOLO_DEVICE = os.getenv("YOLO_DEVICE", "cpu")  # cpu or cuda
    YOLO_CLASSES_FILE = os.getenv("YOLO_CLASSES_FILE", "ml/models/new_model/classes.txt")
    YOLO_CONF_THRESHOLD = float(os.getenv("YOLO_CONF_THRESHOLD", 0.4))
    YOLO_IOU_THRESHOLD = float(os.getenv("YOLO_IOU_THRESHOLD", 0.45))

    # ------------------ Camera + ESP32 ------------------
    CAMERA_API_KEY = os.getenv("CAMERA_API_KEY", "smart_secret_key")
    SERVER_URL = os.getenv("SERVER_URL", "http://127.0.0.1:5000/api/frame")
    CAPTURE_POST_INTERVAL = float(os.getenv("CAPTURE_POST_INTERVAL", 2.0))

    # ESP32 Stream and Alert URLs
    ESP32_URL = os.getenv("ESP32_URL", None)  # e.g. "http://192.168.137.231"
    CAMERA_SOURCE = ESP32_URL  # main live feed source

    # Only define ESP32_ALERT_URL if ESP32_URL is set
    ESP32_ALERT_URL = f"{ESP32_URL}" if ESP32_URL else None

    # ------------------ Email Cooldown ------------------
    EMAIL_COOLDOWN_SECONDS = int(os.getenv("EMAIL_COOLDOWN_SECONDS", 30))
    EMAIL_COOLDOWN_SCOPE = os.getenv("EMAIL_COOLDOWN_SCOPE", "global")  # or "per_criminal"
