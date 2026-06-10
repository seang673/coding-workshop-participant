from flask import Blueprint, request

from app import db
from app.models.deliverable import Deliverable, Dependency, DependencyType
from app.models.user import SystemRole
from app.auth.middleware import require_auth, require_role, get_jwt_identity_uuid
from app.api.helpers import success, created, error, not_found

bp = Blueprint("dependencies", __name__)


def serialize_dependency(dep: Dependency) -> dict:
    return {
        "id": str(dep.id),
        "from_deliverable_id": str(dep.from_deliverable_id),
        "from_title": dep.from_deliverable.title,
        "to_deliverable_id": str(dep.to_deliverable_id),
        "to_title": dep.to_deliverable.title,
        "dependency_type": dep.dependency_type.value,
        "created_at": dep.created_at.isoformat() if dep.created_at else None,
    }


def _would_create_cycle(from_id, to_id) -> bool:
    """
    Check if adding from_id -> to_id would create a circular dependency.
    Uses iterative BFS to walk all descendants of to_id.
    If from_id is reachable from to_id, adding this edge creates a cycle.
    """
    visited = set()
    queue = [str(to_id)]
    while queue:
        current = queue.pop(0)
        if current == str(from_id):
            return True
        if current in visited:
            continue
        visited.add(current)
        downstream = Dependency.query.filter_by(from_deliverable_id=current).all()
        queue.extend(str(d.to_deliverable_id) for d in downstream)
    return False


# ------------------------------------------------------------------
# GET /projects/<pid>/deliverables/<did>/dependencies
# ------------------------------------------------------------------
@bp.route(
    "/projects/<uuid:project_id>/deliverables/<uuid:deliverable_id>/dependencies",
    methods=["GET"]
)
@require_auth
def list_dependencies(project_id, deliverable_id):
    """
    Return dependencies for a deliverable.
    ?direction=blocking  — deliverables this one blocks (outgoing edges)
    ?direction=blocked_by — deliverables blocking this one (incoming edges)
    Default returns both.
    """
    d = db.session.get(Deliverable, deliverable_id)
    if not d or str(d.project_id) != str(project_id):
        return not_found("Deliverable")

    direction = request.args.get("direction", "both")

    result = {}
    if direction in ("blocking", "both"):
        result["blocking"] = [serialize_dependency(dep) for dep in d.blocking]
    if direction in ("blocked_by", "both"):
        result["blocked_by"] = [serialize_dependency(dep) for dep in d.blocked_by]

    return success(result)


# ------------------------------------------------------------------
# POST /projects/<pid>/deliverables/<did>/dependencies
# ------------------------------------------------------------------
@bp.route(
    "/projects/<uuid:project_id>/deliverables/<uuid:deliverable_id>/dependencies",
    methods=["POST"]
)
@require_role(SystemRole.admin, SystemRole.project_manager)
def create_dependency(project_id, deliverable_id):
    """
    Create a dependency: deliverable_id -> to_deliverable_id.
    Body: { to_deliverable_id, dependency_type? }
    Validates: no self-reference, no cross-project, no duplicate, no cycles.
    """
    from_d = db.session.get(Deliverable, deliverable_id)
    if not from_d or str(from_d.project_id) != str(project_id):
        return not_found("Deliverable")

    data = request.get_json(silent=True) or {}
    if not data.get("to_deliverable_id"):
        return error("to_deliverable_id is required")

    to_id = data["to_deliverable_id"]

    if str(to_id) == str(deliverable_id):
        return error("A deliverable cannot depend on itself")

    to_d = db.session.get(Deliverable, to_id)
    if not to_d:
        return not_found("Target deliverable")
    if str(to_d.project_id) != str(project_id):
        return error("Both deliverables must belong to the same project")

    # Duplicate check
    existing = Dependency.query.filter_by(
        from_deliverable_id=deliverable_id,
        to_deliverable_id=to_id,
    ).first()
    if existing:
        return error("This dependency already exists", 409)

    # Cycle detection
    if _would_create_cycle(deliverable_id, to_id):
        return error(
            "Adding this dependency would create a circular dependency chain",
            details={"hint": "Check the existing dependency graph for loops"}
        )

    dep_type = DependencyType.finish_to_start
    if raw_type := data.get("dependency_type"):
        try:
            dep_type = DependencyType(raw_type)
        except ValueError:
            return error(f"Invalid dependency_type. Must be one of: {[t.value for t in DependencyType]}")

    dep = Dependency(
        from_deliverable_id=deliverable_id,
        to_deliverable_id=to_id,
        dependency_type=dep_type,
    )
    db.session.add(dep)
    db.session.commit()
    return created(serialize_dependency(dep), "Dependency created")


# ------------------------------------------------------------------
# DELETE /projects/<pid>/deliverables/<did>/dependencies/<dep_id>
# ------------------------------------------------------------------
@bp.route(
    "/projects/<uuid:project_id>/deliverables/<uuid:deliverable_id>/dependencies/<uuid:dep_id>",
    methods=["DELETE"]
)
@require_role(SystemRole.admin, SystemRole.project_manager)
def delete_dependency(project_id, deliverable_id, dep_id):
    dep = db.session.get(Dependency, dep_id)
    if not dep or str(dep.from_deliverable_id) != str(deliverable_id):
        return not_found("Dependency")
    db.session.delete(dep)
    db.session.commit()
    return success(message="Dependency removed")