# models/event.py
from datetime import datetime
from extensions import db

class Event(db.Model):
    __tablename__ = "weapon_events"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    weapon_detected = db.Column(db.Boolean, default=False)
    confidence = db.Column(db.Float)
    annotated_url = db.Column(db.String(512))
    local_path = db.Column(db.String(512))
    alert_sent = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Event {self.id} | weapon={self.weapon_detected} | conf={self.confidence}>"
