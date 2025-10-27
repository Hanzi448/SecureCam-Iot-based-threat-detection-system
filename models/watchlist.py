# models/watchlist.py
from datetime import datetime
from extensions import db

class Watchlist(db.Model):
    __tablename__ = "watchlist"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    image_url = db.Column(db.String(512))
    embedding = db.Column(db.LargeBinary)  # store FaceNet embedding
    embedding_norm = db.Column(db.Float)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Watchlist {self.id}: {self.name}>"
