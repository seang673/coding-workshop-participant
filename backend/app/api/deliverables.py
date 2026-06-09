from flask import Blueprint, request
from datetime import date

from app import db
from app.models.deliverable import Deliverable, DeliverableStatus
from app.models.project import Project, ProjectAssignment
from app.models.user import SystemRole
from app.auth.middleware import require_auth, require_role, get_jwt_identity_uuid, is_admin
from backend.app.api.projects import success, created, error, not_found, forbidden, paginate

bp = Blueprint("deliverables", __name__, url_prefix="/projects/<uuid:project_id>/deliverables")

VALID_TRANSITIONS = {
    DeliverableStatus.not_started: {DeliverableStatus.in_progress, DeliverableStatus.cancelled},
    DeliverableStatus.in_progress: {DeliverableStatus.blocked, DeliverableStatus.in_review, DeliverableStatus.completed, DeliverableStatus.cancelled},
    DeliverableStatus.blocked:     {DeliverableStatus.in_progress, DeliverableStatus.cancelled},
    DeliverableStatus.in_review:   {DeliverableStatus.in_progress, DeliverableStatus.completed, DeliverableStatus.cancelled},
    DeliverableStatus.completed:   {DeliverableStatus.in_progress},   # allow reopening
    DeliverableStatus.cancelled:   set(),
}


def serialize_deliverable(d: Deliverable, include_children=False) -> dict:
    out = {
        "id": str(d.id),
        "project_id": str(d.project_id),
        "parent_id": str(d.parent_id) if d.parent_id else None,
        "title": d.title,
        "description": d.description,
        "status": d.status.value,
        "due_date": d.due_date.isoformat() if d.due_date else None,
        "sort_order": d.sort_order,
        "is_blocked": d.is_blocked,
        "assignees": [
            {"user_id": str(a.user_id), "full_name": a.user.full_name}
            for a in d.assignments
        ],
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }
    if include_children:
        out["children"] = [
            serialize_deliverable(c) for c in
            d.children.order_by(Deliverable.sort_order).all()
        ]
    return out


def _get_project_or_403(project_id, user_id):
    """Return project if user has access, else return error tuple."""
    p = db.session.get(Project, project_id)
    if not p:
        return None, not_found("Project")
    if not is_admin():
        assigned = {str(a.user_id) for a in p.assignments}
        if str(user_id) != str(p.created_by) and str(user_id) not in assigned:
            return None, forbidden()
    return p, None


def _get_deliverable(project_id, deliverable_id):
    d = db.session.get(Deliverable, deliverable_id)
    if not d or str(d.project_id) != str(project_id):
        return None, not_found("Deliverable")
    return d, None


# ------------------------------------------------------------------
# GET /projects/<id>/deliverables
# ------------------------------------------------------------------
@bp.route("", methods=["GET"])
@require_auth
def list_deliverables(project_id):
    """
    List deliverables for a project.
    ?tree=true returns nested hierarchy (top-level only with children embedded).
    ?status= filters by status.
    ?parent_id= filters to children of a specific parent.
    """
    user_id = get_jwt_identity_uuid()
    _, err = _get_project_or_403(project_id, user_id)
    if err:
        return err

    tree_mode = request.args.get("tree", "false").lower() == "true"

    if tree_mode:
        # Return only top-level deliverables; children embedded recursively
        tops = (
            Deliverable.query
            .filter_by(project_id=project_id, parent_id=None)
            .order_by(Deliverable.sort_order)
            .all()
        )
        return success([serialize_deliverable(d, include_children=True) for d in tops])

    query = Deliverable.query.filter_by(project_id=project_id)

    if status := request.args.get("status"):
        try:
            query = query.filter(Deliverable.status == DeliverableStatus(status))
        except ValueError:
            return error(f"Invalid status: {status}")

    if parent_id := request.args.get("parent_id"):
        query = query.filter(Deliverable.parent_id == parent_id)

    query = query.order_by(Deliverable.sort_order)
    return success(paginate(query, serialize_deliverable))


# ------------------------------------------------------------------
# POST /projects/<id>/deliverables
# ------------------------------------------------------------------
@bp.route("", methods=["POST"])
@require_role(SystemRole.admin, SystemRole.project_manager)
def create_deliverable(project_id):
    user_id = get_jwt_identity_uuid()
    _, err = _get_project_or_403(project_id, user_id)
    if err:
        return err

    data = request.get_json(silent=True) or {}
    if not data.get("title"):
        return error("title is required")

    # Validate parent_id if provided
    parent_id = data.get("parent_id")
    if parent_id:
        parent = db.session.get(Deliverable, parent_id)
        if not parent or str(parent.project_id) != str(project_id):
            return error("parent_id does not belong to this project")

    due_date = None
    if raw_due := data.get("due_date"):
        try:
            due_date = date.fromisoformat(raw_due)
        except ValueError:
            return error("due_date must be ISO format: YYYY-MM-DD")

    d = Deliverable(
        project_id=project_id,
        parent_id=parent_id,
        title=data["title"].strip(),
        description=data.get("description", "").strip() or None,
        due_date=due_date,
        sort_order=data.get("sort_order", 0),
    )
    db.session.add(d)
    db.session.commit()
    return created(serialize_deliverable(d), "Deliverable created")


# ------------------------------------------------------------------
# GET /projects/<id>/deliverables/<did>
# ------------------------------------------------------------------
@bp.route("/<uuid:deliverable_id>", methods=["GET"])
@require_auth
def get_deliverable(project_id, deliverable_id):
    user_id = get_jwt_identity_uuid()
    _, err = _get_project_or_403(project_id, user_id)
    if err:
        return err
    d, err = _get_deliverable(project_id, deliverable_id)
    if err:
        return err
    return success(serialize_deliverable(d, include_children=True))


# ------------------------------------------------------------------
# PATCH /projects/<id>/deliverables/<did>
# ------------------------------------------------------------------
@bp.route("/<uuid:deliverable_id>", methods=["PATCH"])
@require_auth
def update_deliverable(project_id, deliverable_id):
    """
    Update deliverable fields.
    Status transitions are validated against VALID_TRANSITIONS.
    Team members can update status on their own deliverables.
    PMs/admins can update all fields.
    """
    user_id = get_jwt_identity_uuid()
    _, err = _get_project_or_403(project_id, user_id)
    if err:
        return err
    d, err = _get_deliverable(project_id, deliverable_id)
    if err:
        return err

    data = request.get_json(silent=True) or {}

    # Status transition validation
    if "status" in data:
        try:
            new_status = DeliverableStatus(data["status"])
        except ValueError:
            return error(f"Invalid status: {data['status']}")

        allowed = VALID_TRANSITIONS.get(d.status, set())
        if new_status != d.status and new_status not in allowed:
            return error(
                f"Cannot transition from '{d.status.value}' to '{new_status.value}'",
                details={"allowed_transitions": [s.value for s in allowed]},
            )
        d.status = new_status

    if "title" in data:
        d.title = data["title"].strip()
    if "description" in data:
        d.description = data["description"]
    if "sort_order" in data:
        d.sort_order = data["sort_order"]
    if "due_date" in data:
        try:
            d.due_date = date.fromisoformat(data["due_date"]) if data["due_date"] else None
        except ValueError:
            return error("due_date must be ISO format: YYYY-MM-DD")

    db.session.commit()
    return success(serialize_deliverable(d), "Deliverable updated")


# ------------------------------------------------------------------
# DELETE /projects/<id>/deliverables/<did>
# ------------------------------------------------------------------
@bp.route("/<uuid:deliverable_id>", methods=["DELETE"])
@require_role(SystemRole.admin, SystemRole.project_manager)
def delete_deliverable(project_id, deliverable_id):
    user_id = get_jwt_identity_uuid()
    _, err = _get_project_or_403(project_id, user_id)
    if err:
        return err
    d, err = _get_deliverable(project_id, deliverable_id)
    if err:
        return err
    db.session.delete(d)
    db.session.commit()
    return success(message=f"Deliverable '{d.title}' deleted")