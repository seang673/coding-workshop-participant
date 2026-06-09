import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_override: dict = None) -> Flask:
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/acme_tracker"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-in-production")

    if config_override:
        app.config.update(config_override)

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so Flask-Migrate can detect them
    from app.models import user, project, deliverable, budget, time_entry  # noqa: F401

    return app