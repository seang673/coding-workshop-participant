from flask import Blueprint, request
from datetime import date, timedelta
from sqlalchemy import func

from app import db
from app.models.budget import TimeEntry
from app.models.deliverable import Deliverable, DeliverableAssignment
from app.models.project import Project, ProjectAssignment
from app.models.user import User, SystemRole
from app.auth.middleware import require_auth, require_role, get_jwt_identity_uuid, is_admin
from app.api.helpers import success, created, error, not_found, forbidden, paginate

bp = Blueprint("time_entries", __name__)


def serialize_entry(e: TimeEntry) -> dict:
    return {
        "id": str(e.id),
        "user_id": str(e.user_id),
        "full_name": e.user.full_name if e.user else None,
        "deliverable_id": str(e.deliverable_id),
        "deliverable_title": e.deliverable.title if e.deliverable else None,
        "hours": float(e.hours),
        "entry_date": e.entry_date.isoformat() if e.entry_date else None,
        "notes": e.notes,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


# ------------------------------------------------------------------
# GET /projects/<pid>/deliverables/<did>/time-entries
# POST /projects/<pid>/deliverables/<did>/time-entries
# ------------------------------------------------------------------
@bp.route(
    "/projects/<uuid:project_id>/deliverables/<uuid:deliverable_id>/time-entries",
    methods=["GET"]
)
@require_auth
def list_time_entries(project_id, deliverable_id):
    """List time entries for a deliverable. Optional ?user_id= filter."""
    d = db.session.get(Deliverable, deliverable_id)
    if not d or str(d.project_id) != str(project_id):
        return not_found("Deliverable")

    query = TimeEntry.query.filter_by(deliverable_id=deliverable_id)

    if uid := request.args.get("user_id"):
        query = query.filter_by(user_id=uid)

    query = query.order_by(TimeEntry.entry_date.desc())
    return success(paginate(query, serialize_entry))


@bp.route(
    "/projects/<uuid:project_id>/deliverables/<uuid:deliverable_id>/time-entries",
    methods=["POST"]
)
@require_auth
def log_time(project_id, deliverable_id):
    """
    Log hours against a deliverable.
    Team members can only log for themselves.
    PMs/admins can log on behalf of any assigned user.
    Body: { hours, entry_date?, notes?, user_id? }
    """
    current_user_id = get_jwt_identity_uuid()

    d = db.session.get(Deliverable, deliverable_id)
    if not d or str(d.project_id) != str(project_id):
        return not_found("Deliverable")

    data = request.get_json(silent=True) or {}

    if not data.get("hours"):
        return error("hours is required")

    try:
        hours = float(data["hours"])
        if hours <= 0 or hours > 24:
            raise ValueError
    except (ValueError, TypeError):
        return error("hours must be a number between 0.1 and 24")

    # Determine who the entry is for
    target_user_id = data.get("user_id")
    if target_user_id and str(target_user_id) != str(current_user_id):
        if not is_admin() and not _is_project_manager_on(project_id, current_user_id):
            return forbidden("Only PMs and admins can log time on behalf of others")
        target_user = db.session.get(User, target_user_id)
        if not target_user:
            return not_found("User")
    else:
        target_user_id = current_user_id

    entry_date = date.today()
    if raw_date := data.get("entry_date"):
        try:
            entry_date = date.fromisoformat(raw_date)
        except ValueError:
            return error("entry_date must be ISO format: YYYY-MM-DD")

    entry = TimeEntry(
        user_id=target_user_id,
        deliverable_id=deliverable_id,
        hours=hours,
        entry_date=entry_date,
        notes=data.get("notes"),
    )
    db.session.add(entry)
    db.session.commit()
    return created(serialize_entry(entry), "Time logged")


# ------------------------------------------------------------------
# DELETE /time-entries/<id>
# ------------------------------------------------------------------
@bp.route("/time-entries/<uuid:entry_id>", methods=["DELETE"])
@require_auth
def delete_time_entry(entry_id):
    """Users can delete their own entries. Admins can delete any."""
    current_user_id = get_jwt_identity_uuid()
    entry = db.session.get(TimeEntry, entry_id)
    if not entry:
        return not_found("Time entry")
    if not is_admin() and str(entry.user_id) != str(current_user_id):
        return forbidden("You can only delete your own time entries")
    db.session.delete(entry)
    db.session.commit()
    return success(message="Time entry deleted")


# ------------------------------------------------------------------
# GET /users/me/time-entries  — personal time log
# ------------------------------------------------------------------
@bp.route("/users/me/time-entries", methods=["GET"])
@require_auth
def my_time_entries():
    """Return the current user's time entries. ?days=30 to control window."""
    user_id = get_jwt_identity_uuid()
    days = request.args.get("days", 30, type=int)
    since = date.today() - timedelta(days=days)

    query = (
        TimeEntry.query
        .filter_by(user_id=user_id)
        .filter(TimeEntry.entry_date >= since)
        .order_by(TimeEntry.entry_date.desc())
    )
    entries = query.all()
    total_hours = sum(float(e.hours) for e in entries)

    return success({
        "entries": [serialize_entry(e) for e in entries],
        "total_hours": round(total_hours, 2),
        "period_days": days,
    })


# ------------------------------------------------------------------
# GET /reports/allocation  — over-allocation report (admin/PM only)
# ------------------------------------------------------------------
@bp.route("/reports/allocation", methods=["GET"])
@require_role(SystemRole.admin, SystemRole.project_manager)
def allocation_report():
    """
    Cross-project allocation report.
    Returns all users with hours logged in the last N days,
    sorted by allocation percentage descending.
    ?days=30 controls the window (default 30).
    """
    days = request.args.get("days", 30, type=int)
    since = date.today() - timedelta(days=days)
    standard_hours = days * (160 / 30)  # pro-rated from 160h/month

    rows = (
        db.session.query(
            TimeEntry.user_id,
            func.sum(TimeEntry.hours).label("total_hours"),
            func.count(TimeEntry.id).label("entry_count"),
        )
        .filter(TimeEntry.entry_date >= since)
        .group_by(TimeEntry.user_id)
        .order_by(func.sum(TimeEntry.hours).desc())
        .all()
    )

    report = []
    for row in rows:
        user = db.session.get(User, row.user_id)
        if not user:
            continue
        total = float(row.total_hours)
        alloc_pct = round((total / standard_hours) * 100, 1)

        # Which projects is this user on?
        assignments = ProjectAssignment.query.filter_by(user_id=row.user_id).all()
        project_ids = [str(a.project_id) for a in assignments]

        report.append({
            "user_id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "total_hours": round(total, 2),
            "entry_count": row.entry_count,
            "allocation_percentage": alloc_pct,
            "over_allocated": alloc_pct > 100,
            "project_count": len(project_ids),
            "project_ids": project_ids,
        })

    over_count = sum(1 for r in report if r["over_allocated"])
    return success({
        "period_days": days,
        "standard_hours": round(standard_hours, 1),
        "total_users_logged": len(report),
        "over_allocated_count": over_count,
        "members": report,
    })


def _is_project_manager_on(project_id, user_id) -> bool:
    from app.models.project import ProjectRole
    a = ProjectAssignment.query.filter_by(
        project_id=project_id, user_id=user_id
    ).first()
    return a and a.project_role == ProjectRole.lead