from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.user import User, SystemRole
from app.auth.utils import hash_password, verify_password, generate_tokens
from app.auth.middleware import require_auth, get_jwt_identity_uuid

bp = Blueprint("auth", __name__, url_prefix="/auth")


# ------------------------------------------------------------------
# POST /auth/register
# ------------------------------------------------------------------
@bp.route("/register", methods=["POST"])
def register():
    """
    Create a new user account.
    Body: { email, password, full_name, system_role? }
    Returns: user object + token pair.

    Note: in production you would restrict who can set system_role
    (e.g. only admins can create admin accounts). For the workshop
    the first registered user can self-assign any role.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Validate required fields
    missing = [f for f in ("email", "password", "full_name") if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 422

    # Validate password strength (minimum 8 chars for workshop)
    if len(data["password"]) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 422

    # Validate role if provided
    role_value = data.get("system_role", SystemRole.team_member.value)
    try:
        role = SystemRole(role_value)
    except ValueError:
        valid = [r.value for r in SystemRole]
        return jsonify({"error": f"Invalid role. Must be one of: {valid}"}), 422

    user = User(
        email=data["email"].lower().strip(),
        password_hash=hash_password(data["password"]),
        full_name=data["full_name"].strip(),
        system_role=role,
    )

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "An account with that email already exists"}), 409

    tokens = generate_tokens(user)
    return jsonify({
        "message": "Account created successfully",
        "user": _serialize_user(user),
        **tokens,
    }), 201


# ------------------------------------------------------------------
# POST /auth/login
# ------------------------------------------------------------------
@bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate a user and return a JWT token pair.
    Body: { email, password }
    Returns: user object + token pair.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 422

    user = User.query.filter_by(email=email).first()

    # Deliberate: same error for wrong email or wrong password (prevents enumeration)
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "This account has been deactivated"}), 403

    tokens = generate_tokens(user)
    return jsonify({
        "message": "Login successful",
        "user": _serialize_user(user),
        **tokens,
    }), 200


# ------------------------------------------------------------------
# POST /auth/refresh
# ------------------------------------------------------------------
@bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    Exchange a valid refresh token for a new access token.
    Requires: Authorization: Bearer <refresh_token>
    """
    from flask_jwt_extended import create_access_token
    claims = get_jwt()
    new_access = create_access_token(
        identity=get_jwt_identity(),
        additional_claims={
            "role": claims.get("role"),
            "full_name": claims.get("full_name"),
            "email": claims.get("email"),
        }
    )
    return jsonify({"access_token": new_access, "token_type": "Bearer"}), 200


# ------------------------------------------------------------------
# GET /auth/me
# ------------------------------------------------------------------
@bp.route("/me", methods=["GET"])
@require_auth
def me():
    """
    Return the currently authenticated user's profile.
    Requires: Authorization: Bearer <access_token>
    """
    user_id = get_jwt_identity_uuid()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": _serialize_user(user)}), 200


# ------------------------------------------------------------------
# PATCH /auth/me
# ------------------------------------------------------------------
@bp.route("/me", methods=["PATCH"])
@require_auth
def update_me():
    """
    Update the current user's full_name or password.
    Cannot change email or role via this endpoint.
    """
    user_id = get_jwt_identity_uuid()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}

    if "full_name" in data:
        user.full_name = data["full_name"].strip()

    if "password" in data:
        if len(data["password"]) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 422
        user.password_hash = hash_password(data["password"])

    db.session.commit()
    return jsonify({"message": "Profile updated", "user": _serialize_user(user)}), 200


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------
def _serialize_user(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "system_role": user.system_role.value,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }