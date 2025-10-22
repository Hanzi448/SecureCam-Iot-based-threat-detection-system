from flask import Flask, jsonify
from config import Config
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    # simple health route
    @app.route("/health")
    def health():
        return jsonify({"status":"ok"})

    # register blueprints later (api, admin, etc.)
    from api.health import bp as health_bp
    app.register_blueprint(health_bp, url_prefix="/api")

    from api.frame_routes import bp as frame_bp
    app.register_blueprint(frame_bp, url_prefix="/api")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
