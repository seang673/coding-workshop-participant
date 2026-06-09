import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_name: str = None) -> Flask:
    app = Flask(__name__)

    from config import config_by_name
    cfg = config_name or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(cfg, config_by_name["default"]))

    # CORS — allow React dev server (3000) and production origin
    CORS(app, resources={
        r"/*": {
            "origins": os.environ.get(
                "ALLOWED_ORIGINS",
                "http://localhost:3000,http://localhost:5173"
            ).split(","),
            "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
        }
    })

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    _register_jwt_handlers(jwt)

    # Models
    from app.models import user, project, deliverable, budget, time_entry  # noqa: F401

    # Error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)

    # Auth blueprint
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    # API blueprints
    from app.api import (
        projects_bp, deliverables_bp, assignments_bp,
        dependencies_bp, budgets_bp, dashboard_bp,
    )
    from app.api.time_entries import bp as time_entries_bp
    from app.api.users import bp as users_bp

    for bp in (
        projects_bp, deliverables_bp, assignments_bp,
        dependencies_bp, budgets_bp, dashboard_bp,
        time_entries_bp, users_bp,
    ):
        app.register_blueprint(bp)

    @app.route("/health")
    def health():
        return {"status": "ok", "env": cfg}, 200

    return app


def _register_jwt_handlers(jwt_manager: JWTManager):
    from flask import jsonify

    @jwt_manager.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": "Unauthorized", "message": reason}), 401

    @jwt_manager.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": "Invalid token", "message": reason}), 422

    @jwt_manager.expired_token_loader
    def expired_token(_header, _data):
        return jsonify({"error": "Token expired", "message": "Please log in again"}), 401

    @jwt_manager.revoked_token_loader
    def revoked_token(_header, _data):
        return jsonify({"error": "Token revoked"}), 401