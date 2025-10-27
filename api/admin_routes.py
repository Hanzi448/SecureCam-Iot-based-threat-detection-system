from flask import Blueprint, render_template
from services.db_ops import fetch_all_events

bp = Blueprint("admin", __name__)

@bp.route("/admin")
def admin_dashboard():
    """Simple dashboard showing detection logs."""
    events = fetch_all_events(limit=100)
    return render_template("admin_dashboard.html", events=events)
