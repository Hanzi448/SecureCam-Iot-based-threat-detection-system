# models/event.py
from datetime import datetime
from extensions import db

class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # image fields
    image_url = db.Column(db.String(1024), nullable=True)   # will store annotated cloud URL
    local_path = db.Column(db.String(1024), nullable=True)

    # weapon fields
    weapon_detected = db.Column(db.Boolean, default=False, nullable=False)
    weapon_conf = db.Column(db.Float, nullable=True)

    # suspicious + generic confidence
    suspicious = db.Column(db.Boolean, default=False, nullable=False)
    confidence = db.Column(db.Float, nullable=True)

    # criminal / watchlist result
    criminal_detected = db.Column(db.Boolean, default=False, nullable=False)
    criminal_name = db.Column(db.String(256), nullable=True)
    match_distance = db.Column(db.Float, nullable=True)

    # alert delivered
    alert_sent = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return (
            f"<Event {self.id} | ts={self.timestamp} | weapon={self.weapon_detected} "
            f"| criminal={self.criminal_detected} | suspicious={self.suspicious} | alert={self.alert_sent}>"
        )
