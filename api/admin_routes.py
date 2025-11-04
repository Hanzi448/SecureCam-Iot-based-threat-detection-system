# quick admin routes (add to api or admin blueprint)
from flask import Blueprint, render_template
from models.event import Event
from models.watchlist import Watchlist

bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/")
def admin_dashboard():
    events = Event.query.order_by(Event.timestamp.desc()).limit(50).all()
    return render_template("admin_dashboard.html", events=events, title="Dashboard")

@bp.route("/add-criminal")
def admin_add_criminal():
    return render_template("add_criminal.html", title="Add Criminal")

@bp.route("/watchlist")
def admin_watchlist():
    w = Watchlist.query.order_by(Watchlist.added_at.desc()).all()
    return render_template("watchlist.html", watchlist=w, title="Watchlist")
