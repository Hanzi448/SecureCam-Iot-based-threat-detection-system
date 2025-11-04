# services/db_ops.py
from extensions import db, socketio
from models.event import Event
from datetime import datetime


def log_event(
    image_url=None,
    local_path=None,
    weapon_detected=False,
    weapon_conf=None,
    suspicious=False,
    confidence=None,
    criminal_detected=False,
    criminal_name=None,
    match_distance=None,
    alert_sent=False
):
    """
    Insert event row using simplified Event schema and emit a socket payload.
    Returns event.id or None on failure.
    """
    try:
        # Safely cast numeric values
        def safe_float(val):
            try:
                return float(val) if val is not None else None
            except (ValueError, TypeError):
                return None

        evt = Event(
            timestamp=datetime.now(),
            image_url=image_url,
            local_path=local_path,
            weapon_detected=bool(weapon_detected),
            weapon_conf=safe_float(weapon_conf),
            suspicious=bool(suspicious),
            confidence=safe_float(confidence),
            criminal_detected=bool(criminal_detected),
            criminal_name=criminal_name,
            match_distance=safe_float(match_distance),
            alert_sent=bool(alert_sent),
        )

        db.session.add(evt)
        db.session.commit()

        payload = {
            "id": evt.id,
            "timestamp": evt.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "image_url": evt.image_url,
            "local_path": evt.local_path,
            "weapon_detected": evt.weapon_detected,
            "weapon_conf": evt.weapon_conf,
            "suspicious": evt.suspicious,
            "confidence": evt.confidence,
            "criminal_detected": evt.criminal_detected,
            "criminal_name": evt.criminal_name,
            "match_distance": evt.match_distance,
            "alert_sent": evt.alert_sent,
        }

        # Emit socket update for dashboard live view
        socketio.emit("new_event", payload, namespace="/")
        print(f"[DB] Event logged & broadcast (ID={evt.id})")
        return evt.id

    except Exception as e:
        db.session.rollback()
        print(f"[DB ERROR] {e}")
        return None
