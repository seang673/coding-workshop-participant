from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from app.models.user import SystemRole


def require_role(*roles: SystemRole):
    """
    Decorator that protects a route to users whose system_role is in `roles`.

    Usage:
        @bp.route("/admin-only")
        @require_role(SystemRole.admin)
        def admin_only(): ...

        @bp.route("/pm-or-admin")
        @require_role(SystemRole.admin, SystemRole.project_manager)
        def pm_or_admin(): ...

    The JWT must be present and valid, or a 401 is returned.
    If the role is not permitted, a 403 is returned.
    """
    allowed = {r.value if isinstance(r, SystemRole) else r for r in roles}

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")
            if user_role not in allowed:
                return jsonify({
                    "error": "Forbidden",
                    "message": f"This action requires one of: {', '.join(allowed)}",
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_auth(fn):
    """
    Lighter decorator — just checks that a valid JWT is present.
    Use when any authenticated user is allowed, regardless of role.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper


def get_jwt_identity_uuid():
    """Return the current user's UUID from the JWT identity claim."""
    from flask_jwt_extended import get_jwt_identity
    import uuid
    return uuid.UUID(get_jwt_identity())


def current_user_role() -> str:
    """Return the current user's role string from JWT claims."""
    return get_jwt().get("role")


def is_admin() -> bool:
    return current_user_role() == SystemRole.admin.value


def is_project_manager() -> bool:
    return current_user_role() in (
        SystemRole.admin.value,
        SystemRole.project_manager.value,
    )