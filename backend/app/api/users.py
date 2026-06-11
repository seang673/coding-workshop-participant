from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.user import User, SystemRole
from app.auth.middleware import require_role, require_auth, get_jwt_identity_uuid
from app.auth.utils import hash_password
from app.api.helpers import success, created, error, not_found, forbidden, paginate

bp = Blueprint("users", __name__, url_prefix="/users")


def serialize_user(u: User) -> dict:
    return {
        "id": str(u.id),
        "email": u.email,
        "full_name": u.full_name,
        "system_role": u.system_role.value,
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


def serialize_user_summary(u: User) -> dict:
    """Serialize the minimal user fields exposed by the search endpoint."""
    return {
        "id": str(u.id),
        "email": u.email,
        "full_name": u.full_name,
    }


# ------------------------------------------------------------------
# GET /users  — admin only
# ------------------------------------------------------------------
@bp.route("", methods=["GET"])
@require_role(SystemRole.admin)
def list_users():
    """
    List all users. Admin only.
    ?role= filter by system_role.
    ?active= filter by is_active (true/false).
    ?search= filter by name or email.
    """
    query = User.query

    if role := request.args.get("role"):
        try:
            query = query.filter_by(system_role=SystemRole(role))
        except ValueError:
            return error(f"Invalid role: {role}")

    if active := request.args.get("active"):
        query = query.filter_by(is_active=active.lower() == "true")

    if search := request.args.get("search"):
        pattern = f"%{search}%"
        query = query.filter(
            db.or_(User.full_name.ilike(pattern), User.email.ilike(pattern))
        )

    query = query.order_by(User.full_name)
    return success(paginate(query, serialize_user))


# ------------------------------------------------------------------
# POST /users  — admin only
# ------------------------------------------------------------------
@bp.route("", methods=["POST"])
@require_role(SystemRole.admin)
def create_user():
    """
    Create a new user account. Admin only.
    Body: { email, password, full_name, system_role }

    Unlike POST /auth/register (self-registration, limited to
    'team_member'/'stakeholder'), admins may create accounts with any role.
    """
    data = request.get_json(silent=True) or {}

    missing = [f for f in ("email", "password", "full_name", "system_role") if not data.get(f)]
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", status=422)

    if len(data["password"]) < 8:
        return error("Password must be at least 8 characters", status=422)

    try:
        role = SystemRole(data["system_role"])
    except ValueError:
        return error(f"Invalid role: {data['system_role']}", status=422)

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
        return error("An account with that email already exists", status=409)

    return created(serialize_user(user), "User created")


# ------------------------------------------------------------------
# GET /users/search — admin or project_manager; minimal fields
# ------------------------------------------------------------------
@bp.route("/search", methods=["GET"])
@require_role(SystemRole.admin, SystemRole.project_manager)
def search_users():
    """
    Search active users by name or email. Admin and project manager only.

    Returns minimal fields (id, full_name, email) for use in pickers such as
    adding a project member, without exposing roles or account status.
    ?search= filters by name or email.
    """
    query = User.query.filter_by(is_active=True)

    if search := request.args.get("search"):
        pattern = f"%{search}%"
        query = query.filter(
            db.or_(User.full_name.ilike(pattern), User.email.ilike(pattern))
        )

    query = query.order_by(User.full_name)
    return success(paginate(query, serialize_user_summary))


# ------------------------------------------------------------------
# GET /users/<id>  — admin, or self
# ------------------------------------------------------------------
@bp.route("/<uuid:user_id>", methods=["GET"])
@require_auth
def get_user(user_id):
    current_id = get_jwt_identity_uuid()
    from app.auth.middleware import is_admin
    if not is_admin() and str(current_id) != str(user_id):
        return forbidden("You can only view your own profile")

    user = db.session.get(User, user_id)
    if not user:
        return not_found("User")
    return success(serialize_user(user))


# ------------------------------------------------------------------
# PATCH /users/<id>  — admin can update role/active; users update themselves
# ------------------------------------------------------------------
@bp.route("/<uuid:user_id>", methods=["PATCH"])
@require_auth
def update_user(user_id):
    """
    Admin: can change system_role and is_active for any user.
    Self: can change full_name and password only.
    """
    from app.auth.middleware import is_admin
    current_id = get_jwt_identity_uuid()
    admin = is_admin()

    if not admin and str(current_id) != str(user_id):
        return forbidden("You can only update your own profile")

    user = db.session.get(User, user_id)
    if not user:
        return not_found("User")

    data = request.get_json(silent=True) or {}

    # Fields any user can update on themselves
    if "full_name" in data:
        user.full_name = data["full_name"].strip()

    if "password" in data:
        if len(data["password"]) < 8:
            return error("Password must be at least 8 characters")
        user.password_hash = hash_password(data["password"])

    # Admin-only fields
    if admin:
        if "system_role" in data:
            try:
                user.system_role = SystemRole(data["system_role"])
            except ValueError:
                return error(f"Invalid role: {data['system_role']}")

        if "is_active" in data:
            # Prevent self-deactivation
            if str(user_id) == str(current_id) and not data["is_active"]:
                return error("You cannot deactivate your own account")
            user.is_active = bool(data["is_active"])

    db.session.commit()
    return success(serialize_user(user), "User updated")


# ------------------------------------------------------------------
# POST /users/<id>/deactivate  — admin only, explicit action
# ------------------------------------------------------------------
@bp.route("/<uuid:user_id>/deactivate", methods=["POST"])
@require_role(SystemRole.admin)
def deactivate_user(user_id):
    current_id = get_jwt_identity_uuid()
    if str(current_id) == str(user_id):
        return error("You cannot deactivate your own account")

    user = db.session.get(User, user_id)
    if not user:
        return not_found("User")
    if not user.is_active:
        return error("User is already deactivated")

    user.is_active = False
    db.session.commit()
    return success(message=f"{user.full_name} has been deactivated")


# ------------------------------------------------------------------
# POST /users/<id>/reactivate  — admin only
# ------------------------------------------------------------------
@bp.route("/<uuid:user_id>/reactivate", methods=["POST"])
@require_role(SystemRole.admin)
def reactivate_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return not_found("User")
    if user.is_active:
        return error("User is already active")

    user.is_active = True
    db.session.commit()
    return success(message=f"{user.full_name} has been reactivated")