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

    from config import config_by_name
    cfg = config_name or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(cfg, config_by_name["default"]))

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    _register_jwt_handlers(jwt)

    # Models — must import before blueprints so Migrate detects them
    from app.models import user, project, deliverable, budget, time_entry  # noqa: F401

    # Auth blueprint
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    # API blueprints
    from app.api import (
        projects_bp, deliverables_bp, assignments_bp,
        dependencies_bp, budgets_bp, dashboard_bp,
    )
    for bp in (projects_bp, deliverables_bp, assignments_bp,
               dependencies_bp, budgets_bp, dashboard_bp):
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