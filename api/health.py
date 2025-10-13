# api/health.py
from flask import Blueprint, jsonify
bp = Blueprint("health", __name__)

@bp.route("/ping")
def ping():
    return jsonify({"ping":"pong"})
