import time
from threading import Lock
from config import Config

_lock = Lock()
_last_sent = {}  # map key -> last_sent_epoch_seconds

def can_send(key: str = "global") -> bool:
    """
    Returns True if an email may be sent for `key` right now.
    This implements a cooldown window defined by Config.EMAIL_COOLDOWN_SECONDS.
    """
    cooldown = getattr(Config, "EMAIL_COOLDOWN_SECONDS", 60)  # default 60s
    now = time.time()
    with _lock:
        last = _last_sent.get(key, 0)
        if now - last >= cooldown:
            _last_sent[key] = now
            return True
        else:
            return False

def force_update(key: str = "global"):
    """Force update last_sent time (useful if you want to record send without calling can_send)."""
    with _lock:
        _last_sent[key] = time.time()
