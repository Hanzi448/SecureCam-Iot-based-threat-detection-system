import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    ENV = os.getenv("FLASK_ENV", "production")
    SECRET_KEY = os.getenv("SECRET_KEY", "change_me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv("REDIS_URL")

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    # SMTP
    GMAIL_USER = os.getenv("GMAIL_USER", "your_email@gmail.com")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "your_app_password")  # app password only
    ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "recipient_email@gmail.com")

    # Thresholds
    WEAPON_CONF_THRESHOLD = float(os.getenv("WEAPON_CONF_THRESHOLD", 0.4))
    FACENET_THRESHOLD = float(os.getenv("FACENET_THRESHOLD", 0.45))
    OCULAR_THRESHOLD = float(os.getenv("OCULAR_THRESHOLD", 0.55))

    # Camera
    CAMERA_API_KEY = os.getenv("CAMERA_API_KEY", "smart_secret_key")

    # Cooldown config
    EMAIL_COOLDOWN_SECONDS = int(os.getenv("EMAIL_COOLDOWN_SECONDS", "60"))
    EMAIL_COOLDOWN_SCOPE = "global"  # or "per_criminal"

    ESP32_URL = "http://192.168.137.127"  # Your working ESP32 stream
    CAMERA_SOURCE = ESP32_URL             # Use ESP32 as main camera source
    SERVER_URL = "http://127.0.0.1:5000/api/frame"
    CAPTURE_POST_INTERVAL = 2.0           # seconds
