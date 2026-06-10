import os
from datetime import timedelta


def _database_url() -> str:
    """Build the SQLAlchemy database URI.

    Local dev/tests set DATABASE_URL explicitly. On Lambda, Terraform injects
    discrete POSTGRES_* env vars (Aurora is VPC-only, no DATABASE_URL) — build
    the URI from those instead.
    """
    if url := os.environ.get("DATABASE_URL"):
        return url
    if host := os.environ.get("POSTGRES_HOST"):
        user = os.environ.get("POSTGRES_USER", "postgres")
        password = os.environ.get("POSTGRES_PASS", "")
        port = os.environ.get("POSTGRES_PORT", "5432")
        name = os.environ.get("POSTGRES_NAME", "postgres")
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    return "postgresql://postgres:password@localhost:5432/coding_workshop_db"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    # Inherits Config's SECRET_KEY/JWT_SECRET_KEY (env var with dev fallback) —
    # Terraform doesn't inject SECRET_KEY/JWT_SECRET_KEY into the Lambda, so a
    # hard `os.environ["..."]` lookup here would return None and break JWT/Flask.
    # Acceptable for this workshop deployment; set real secrets via Lambda env
    # vars for a production deployment.


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}