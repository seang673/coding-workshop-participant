from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt
from datetime import timezone
import uuid


def hash_password(plain: str) -> str:
    """Hash a plain-text password using werkzeug's pbkdf2 method."""
    return generate_password_hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored hash."""
    return check_password_hash(hashed, plain)


def generate_tokens(user) -> dict:
    """
    Generate an access + refresh token pair for a user.
    The JWT identity is the user's UUID string.
    Additional claims carry role and name so routes don't need a DB hit
    just to check authorization.
    """
    identity = str(user.id)
    additional_claims = {
        "role": user.system_role.value,
        "full_name": user.full_name,
        "email": user.email,
    }
    access_token = create_access_token(
        identity=identity,
        additional_claims=additional_claims
    )
    refresh_token = create_refresh_token(
        identity=identity,
        additional_claims=additional_claims
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }


def get_current_claims() -> dict:
    """Return the decoded JWT claims for the current request."""
    return get_jwt()