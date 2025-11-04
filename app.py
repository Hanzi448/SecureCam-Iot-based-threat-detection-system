# app.py
from flask import Flask, jsonify, render_template
from config import Config
from extensions import db, socketio


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    socketio.init_app(app)

    # Register blueprints

    from api.frame_routes import bp as frame_bp
    app.register_blueprint(frame_bp, url_prefix="/api")

    from api.admin_routes import bp as admin_bp
    app.register_blueprint(admin_bp)

    from api.watchlist_routes import bp as watchlist_bp
    app.register_blueprint(watchlist_bp, url_prefix="/api")

    from api.camera_routes import bp as camera_bp
    app.register_blueprint(camera_bp)

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/live")
    def live_window():
        return render_template("live_window.html")

    return app


if __name__ == "__main__":
    app = create_app()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
