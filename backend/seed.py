"""
Seed script — populates the database with realistic ACME Inc. sample data.

Usage:
    DATABASE_URL=postgresql://... python seed.py

Idempotent: running it twice will not duplicate data (checks for existing users first).

The actual seed data lives in `app.seed` (so it's bundled with the Lambda
deployment package and reusable from `app/function.py`'s `_migrate` action).
This script just provides the local CLI entrypoint.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.seed import run

app = create_app("development")

if __name__ == "__main__":
    with app.app_context():
        run()
