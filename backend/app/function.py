"""
AWS Lambda entrypoint for the ACME Project Tracker Flask app.

Terraform (`infra/locals.tf`) auto-discovers Lambda services by scanning
`backend/<service>/function.py` and zips that directory's *contents* at the
zip root (no enclosing `<service>/` directory in the package). Every module
in this app uses absolute `from app.xxx import ...` imports, so before those
imports run we register this directory itself as the `app` package.
"""
import os
import sys
import importlib.util

os.environ.setdefault("FLASK_ENV", "production")

if "app" not in sys.modules:
    _here = os.path.dirname(os.path.abspath(__file__))
    _spec = importlib.util.spec_from_file_location(
        "app", os.path.join(_here, "__init__.py"), submodule_search_locations=[_here]
    )
    _app_module = importlib.util.module_from_spec(_spec)
    sys.modules["app"] = _app_module
    _spec.loader.exec_module(_app_module)

from apig_wsgi import make_lambda_handler  # noqa: E402
from app import create_app, db  # noqa: E402

flask_app = create_app()
_wsgi_handler = make_lambda_handler(flask_app, binary_support=True)

# CloudFront forwards the full matched path (e.g. /api/app/health) to this
# Lambda's Function URL unmodified. The LocalStack dev proxy
# (bin/proxy-server.js) already strips the /api/<service> prefix before
# forwarding, so only strip it here if it's still present.
PATH_PREFIX = "/api/app"

# Trigger that keeps `updated_at` current on UPDATE — mirrors the TRIGGERS
# section of backend/migrations/schema.sql (kept inline here so it ships in
# the Lambda package, which only contains this directory's contents).
_TRIGGERS_SQL = """
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE OR REPLACE TRIGGER trg_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE OR REPLACE TRIGGER trg_deliverables_updated_at
    BEFORE UPDATE ON deliverables
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
"""


def handler(event, context):
    """Lambda entrypoint: dispatch one-off actions or proxy to the Flask app via WSGI."""
    if event.get("action") == "migrate":
        return _migrate()

    raw_path = event.get("rawPath", "")
    if raw_path.startswith(PATH_PREFIX):
        event["rawPath"] = raw_path[len(PATH_PREFIX):] or "/"

    return _wsgi_handler(event, context)


def _migrate():
    """Create the schema (if needed), apply triggers, and seed sample data.

    Invoked directly (not via the Function URL) since Aurora is VPC-only:

        aws lambda invoke --function-name <name> \\
            --cli-binary-format raw-in-base64-out \\
            --payload '{"action": "migrate"}' /tmp/result.json

    Idempotent: db.create_all() skips existing tables, CREATE OR REPLACE
    handles the trigger function/triggers, and app.seed.run() checks for
    existing seed data before inserting.
    """
    from app import seed

    with flask_app.app_context():
        db.create_all()

        raw_conn = db.engine.raw_connection()
        try:
            raw_conn.cursor().execute(_TRIGGERS_SQL)
            raw_conn.commit()
        finally:
            raw_conn.close()

        seed.run()

    return {"statusCode": 200, "body": "migration + seed complete"}
