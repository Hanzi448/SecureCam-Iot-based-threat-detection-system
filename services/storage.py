# services/storage.py
import cloudinary
import cloudinary.uploader
from config import Config

cloudinary.config(
  cloud_name=Config.CLOUDINARY_CLOUD_NAME,
  api_key=Config.CLOUDINARY_API_KEY,
  api_secret=Config.CLOUDINARY_API_SECRET,
  secure=True
)

def upload_image(local_path, folder="events"):
    res = cloudinary.uploader.upload(local_path, folder=folder)
    return res.get("secure_url")
