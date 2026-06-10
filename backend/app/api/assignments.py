from flask import Blueprint, request

from app import db
from app.models.project import Project, ProjectAssignment, ProjectRole
from app.models.deliverable import Deliverable, DeliverableAssignment
from app.models.user import User, SystemRole
from app.auth.middleware import require_role, require_auth, get_jwt_identity_uuid, is_admin
from app.api.helpers import success, created, error, not_found, forbidden

bp = Blueprint("assignments", __name__)


# ================================================================
# PROJECT ASSIGNMENTS  — /projects/<id>/members
# ================================================================

@bp.route("/projects/<uuid:project_id>/members", methods=["GET"])
@require_auth
def list_project_members(project_id):
    """List all members assigned to a project."""
    project = db.session.get(Project, project_id)
    if not project:
        return not_found("Project")
    return success([
        {
            "user_id": str(a.user_id),
            "full_name": a.user.full_name,
            "email": a.user.email,
            "project_role": a.project_role.value,
            "assigned_at": a.assigned_at.isoformat() if a.assigned_at else None,
        }
        for a in project.assignments
    ])


@bp.route("/projects/<uuid:project_id>/members", methods=["POST"])
@require_role(SystemRole.admin, SystemRole.project_manager)
def add_project_member(project_id):
    """
    Add a user to a project with a given project_role.
    Body: { user_id, project_role? }
    """
    project = db.session.get(Project, project_id)
    if not project:
        return not_found("Project")

    # PMs can only manage their own projects
    user_id = get_jwt_identity_uuid()
    if not is_admin() and str(project.created_by) != str(user_id):
        assigned_ids = {str(a.user_id) for a in project.assignments
                       if a.project_role == ProjectRole.lead}
        if str(user_id) not in assigned_ids:
            return forbidden("Only the project lead or an admin can add members")

    data = request.get_json(silent=True) or {}
    if not data.get("user_id"):
        return error("user_id is required")

    target_user = db.session.get(User, data["user_id"])
    if not target_user:
        return not_found("User")

    role_value = data.get("project_role", ProjectRole.contributor.value)
    try:
        role = ProjectRole(role_value)
    except ValueError:
        return error(f"Invalid project_role. Must be one of: {[r.value for r in ProjectRole]}")

    # Check if already assigned
    existing = ProjectAssignment.query.filter_by(
        project_id=project_id, user_id=data["user_id"]
    ).first()
    if existing:
        existing.project_role = role
        db.session.commit()
        return success(message="Member role updated")

    assignment = ProjectAssignment(
        project_id=project_id,
        user_id=data["user_id"],
        project_role=role,
    )
    db.session.add(assignment)
    db.session.commit()
    return created(message=f"{target_user.full_name} added to project as {role.value}")


@bp.route("/projects/<uuid:project_id>/members/<uuid:user_id>", methods=["DELETE"])
@require_role(SystemRole.admin, SystemRole.project_manager)
def remove_project_member(project_id, user_id):
    """Remove a user from a project."""
    assignment = ProjectAssignment.query.filter_by(
        project_id=project_id, user_id=user_id
    ).first()
    if not assignment:
        return not_found("Assignment")

    # Prevent removing the only lead
    if assignment.project_role == ProjectRole.lead:
        other_leads = ProjectAssignment.query.filter_by(
            project_id=project_id,
            project_role=ProjectRole.lead,
        ).filter(ProjectAssignment.user_id != user_id).count()
        if other_leads == 0:
            return error("Cannot remove the only project lead. Assign another lead first.")

    db.session.delete(assignment)
    db.session.commit()
    return success(message="Member removed from project")


# ================================================================
# DELIVERABLE ASSIGNMENTS  — /projects/<pid>/deliverables/<did>/assignees
# ================================================================

@bp.route(
    "/projects/<uuid:project_id>/deliverables/<uuid:deliverable_id>/assignees",
    methods=["GET"]
)
@require_auth
def list_deliverable_assignees(project_id, deliverable_id):
    d = db.session.get(Deliverable, deliverable_id)
    if not d or str(d.project_id) != str(project_id):
        return not_found("Deliverable")
    return success([
        {
            "user_id": str(a.user_id),
            "full_name": a.user.full_name,
            "email": a.user.email,
            "assigned_at": a.assigned_at.isoformat() if a.assigned_at else None,
        }
        for a in d.assignments
    ])


@bp.route(
    "/projects/<uuid:project_id>/deliverables/<uuid:deliverable_id>/assignees",
    methods=["POST"]
)
@require_role(SystemRole.admin, SystemRole.project_manager)
def assign_deliverable(project_id, deliverable_id):
    """Assign a user to a deliverable. Body: { user_id }"""
    d = db.session.get(Deliverable, deliverable_id)
    if not d or str(d.project_id) != str(project_id):
        return not_found("Deliverable")

    data = request.get_json(silent=True) or {}
    if not data.get("user_id"):
        return error("user_id is required")

    target_user = db.session.get(User, data["user_id"])
    if not target_user:
        return not_found("User")

    existing = DeliverableAssignment.query.filter_by(
        deliverable_id=deliverable_id, user_id=data["user_id"]
    ).first()
    if existing:
        return error("User is already assigned to this deliverable", 409)

    assignment = DeliverableAssignment(
        deliverable_id=deliverable_id,
        user_id=data["user_id"],
    )
    db.session.add(assignment)
    db.session.commit()
    return created(message=f"{target_user.full_name} assigned to deliverable")


@bp.route(
    "/projects/<uuid:project_id>/deliverables/<uuid:deliverable_id>/assignees/<uuid:user_id>",
    methods=["DELETE"]
)
@require_role(SystemRole.admin, SystemRole.project_manager)
def unassign_deliverable(project_id, deliverable_id, user_id):
    assignment = DeliverableAssignment.query.filter_by(
        deliverable_id=deliverable_id, user_id=user_id
    ).first()
    if not assignment:
        return not_found("Assignment")
    db.session.delete(assignment)
    db.session.commit()
    return success(message="User unassigned from deliverable")