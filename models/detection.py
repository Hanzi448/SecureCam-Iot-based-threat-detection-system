from extensions import db

class Detection(db.Model):
    __tablename__ = "detections"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"))
    label = db.Column(db.String(120))
    conf = db.Column(db.Float)
    bbox = db.Column(db.JSON)  # store as json [x1,y1,x2,y2]
