# services/db_ops.py
from extensions import db, socketio
from models.event import Event

def log_event(weapon_detected, confidence, annotated_url, local_path, alert_sent):
    """Insert a new event into the database and notify dashboard."""
    try:
        event = Event(
            weapon_detected=weapon_detected,
            confidence=confidence,
            annotated_url=annotated_url,
            local_path=local_path,
            alert_sent=alert_sent
        )
        db.session.add(event)
        db.session.commit()

        # Emit socket event for real-time updates
        socketio.emit("new_event", {
            "id": event.id,
            "timestamp": event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "weapon_detected": event.weapon_detected,
            "confidence": event.confidence,
            "annotated_url": event.annotated_url,
            "alert_sent": event.alert_sent
        })

        print(f"[DB] Event logged & broadcast (ID={event.id})")
        return event.id
    except Exception as e:
        db.session.rollback()
        print(f"[DB ERROR] {e}")
        return None

def fetch_all_events(limit=50):
    """Fetch the latest N events for dashboard."""
    try:
        return Event.query.order_by(Event.timestamp.desc()).limit(limit).all()
    except Exception as e:
        print(f"[DB ERROR] Could not fetch events: {e}")
        return []
