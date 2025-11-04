from extensions import db
from datetime import datetime

class Camera(db.Model):
    __tablename__ = "cameras"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    location = db.Column(db.Text)
    api_key = db.Column(db.String(256))
    rotate = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
