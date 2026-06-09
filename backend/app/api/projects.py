from flask import Blueprint, request
from sqlalchemy import or_

from app import db
from app.models.project import Project, ProjectAssignment, ProjectStatus, ProjectRole
from app.models.user import SystemRole
from app.auth.middleware import require_auth, require_role, get_jwt_identity_uuid, is_admin
from backend.app.api.projects import success, created, error, not_found, forbidden, paginate

bp = Blueprint("projects", __name__, url_prefix="/projects")


# ------------------------------------------------------------------
# Serializers
# ------------------------------------------------------------------
def serialize_project(p: Project, detail=False) -> dict:
    base = {
        "id": str(p.id),
        "name": p.name,
        "description": p.description,
        "department": p.department,
        "status": p.status.value,
        "start_date": p.start_date.isoformat() if p.start_date else None,
        "end_date": p.end_date.isoformat() if p.end_date else None,
        "created_by": str(p.created_by),
        "completion_percentage": p.completion_percentage,
        "total_planned_budget": float(p.total_planned_budget),
        "total_actual_spend": float(p.total_actual_spend),
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }
    if detail:
        base["members"] = [
            {
                "user_id": str(a.user_id),
                "full_name": a.user.full_name,
                "email": a.user.email,
                "project_role": a.project_role.value,
            }
            for a in p.assignments
        ]
    return base


def _get_accessible_project(project_id, user_id, admin):
    """Fetch project and verify current user has access."""
    p = db.session.get(Project, project_id)
    if not p:
        return None, not_found("Project")
    if not admin:
        assigned_ids = {str(a.user_id) for a in p.assignments}
        if str(user_id) != str(p.created_by) and str(user_id) not in assigned_ids:
            return None, forbidden()
    return p, None


# ------------------------------------------------------------------
# GET /projects
# ------------------------------------------------------------------
@bp.route("", methods=["GET"])
@require_auth
def list_projects():
    """
    List projects accessible to the current user.
    Admins see all. PMs and members see only their own.
    Query params: status, department, search, page, per_page
    """
    user_id = get_jwt_identity_uuid()
    admin = is_admin()

    query = Project.query

    if not admin:
        # Join through assignments to find projects user is on, or created
        assigned = db.session.query(ProjectAssignment.project_id).filter_by(user_id=user_id)
        query = query.filter(
            or_(Project.created_by == user_id, Project.id.in_(assigned))
        )

    # Filters
    if status := request.args.get("status"):
        try:
            query = query.filter(Project.status == ProjectStatus(status))
        except ValueError:
            return error(f"Invalid status value: {status}")

    if dept := request.args.get("department"):
        query = query.filter(Project.department.ilike(f"%{dept}%"))

    if search := request.args.get("search"):
        query = query.filter(Project.name.ilike(f"%{search}%"))

    query = query.order_by(Project.end_date.asc())
    return success(paginate(query, serialize_project))


# ------------------------------------------------------------------
# POST /projects
# ------------------------------------------------------------------
@bp.route("", methods=["POST"])
@require_role(SystemRole.admin, SystemRole.project_manager)
def create_project():
    """Create a new project. Automatically assigns creator as lead."""
    data = request.get_json(silent=True) or {}
    user_id = get_jwt_identity_uuid()

    missing = [f for f in ("name", "start_date", "end_date") if not data.get(f)]
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}")

    try:
        from datetime import date
        start = date.fromisoformat(data["start_date"])
        end = date.fromisoformat(data["end_date"])
    except ValueError:
        return error("start_date and end_date must be ISO format: YYYY-MM-DD")

    if end <= start:
        return error("end_date must be after start_date")

    status = ProjectStatus.draft
    if raw_status := data.get("status"):
        try:
            status = ProjectStatus(raw_status)
        except ValueError:
            return error(f"Invalid status: {raw_status}")

    project = Project(
        name=data["name"].strip(),
        description=data.get("description", "").strip() or None,
        department=data.get("department", "").strip() or None,
        status=status,
        start_date=start,
        end_date=end,
        created_by=user_id,
    )
    db.session.add(project)
    db.session.flush()  # get the ID before committing

    # Auto-assign creator as lead
    assignment = ProjectAssignment(
        project_id=project.id,
        user_id=user_id,
        project_role=ProjectRole.lead,
    )
    db.session.add(assignment)
    db.session.commit()

    return created(serialize_project(project, detail=True), "Project created")


# ------------------------------------------------------------------
# GET /projects/<id>
# ------------------------------------------------------------------
@bp.route("/<uuid:project_id>", methods=["GET"])
@require_auth
def get_project(project_id):
    user_id = get_jwt_identity_uuid()
    project, err = _get_accessible_project(project_id, user_id, is_admin())
    if err:
        return err
    return success(serialize_project(project, detail=True))


# ------------------------------------------------------------------
# PATCH /projects/<id>
# ------------------------------------------------------------------
@bp.route("/<uuid:project_id>", methods=["PATCH"])
@require_role(SystemRole.admin, SystemRole.project_manager)
def update_project(project_id):
    """Update project fields. PMs can only update their own projects."""
    user_id = get_jwt_identity_uuid()
    project, err = _get_accessible_project(project_id, user_id, is_admin())
    if err:
        return err

    data = request.get_json(silent=True) or {}

    if "name" in data:
        project.name = data["name"].strip()
    if "description" in data:
        project.description = data["description"]
    if "department" in data:
        project.department = data["department"]
    if "status" in data:
        try:
            project.status = ProjectStatus(data["status"])
        except ValueError:
            return error(f"Invalid status: {data['status']}")
    if "start_date" in data:
        from datetime import date
        try:
            project.start_date = date.fromisoformat(data["start_date"])
        except ValueError:
            return error("start_date must be ISO format: YYYY-MM-DD")
    if "end_date" in data:
        from datetime import date
        try:
            project.end_date = date.fromisoformat(data["end_date"])
        except ValueError:
            return error("end_date must be ISO format: YYYY-MM-DD")

    if project.end_date <= project.start_date:
        return error("end_date must be after start_date")

    db.session.commit()
    return success(serialize_project(project, detail=True), "Project updated")


# ------------------------------------------------------------------
# DELETE /projects/<id>
# ------------------------------------------------------------------
@bp.route("/<uuid:project_id>", methods=["DELETE"])
@require_role(SystemRole.admin)
def delete_project(project_id):
    """Hard delete. Admin only. Cascades to all deliverables, assignments, budgets."""
    project = db.session.get(Project, project_id)
    if not project:
        return not_found("Project")
    db.session.delete(project)
    db.session.commit()
    return success(message=f"Project '{project.name}' deleted")