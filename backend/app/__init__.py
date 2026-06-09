import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_name: str = None) -> Flask:
    app = Flask(__name__)

    # Load config
    from config import config_by_name
    cfg = config_name or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(cfg, config_by_name["default"]))

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register JWT error handlers
    _register_jwt_handlers(jwt)

    # Import models so Flask-Migrate can detect them
    from app.models import user, project, deliverable, budget, time_entry  # noqa: F401

    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    # Health check
    @app.route("/health")
    def health():
        return {"status": "ok", "env": cfg}, 200

    return app


def _register_jwt_handlers(jwt_manager: JWTManager):
    """Clean JSON error responses for JWT failures."""
    from flask import jsonify

    @jwt_manager.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": "Unauthorized", "message": reason}), 401

    @jwt_manager.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": "Invalid token", "message": reason}), 422

    @jwt_manager.expired_token_loader
    def expired_token(_jwt_header, _jwt_data):
        return jsonify({"error": "Token expired", "message": "Please log in again"}), 401

    @jwt_manager.revoked_token_loader
    def revoked_token(_jwt_header, _jwt_data):
        return jsonify({"error": "Token revoked"}), 401