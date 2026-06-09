from flask import Blueprint
from datetime import date, timedelta
from sqlalchemy import func, or_

from app import db
from app.models.project import Project, ProjectAssignment, ProjectStatus
from app.models.deliverable import Deliverable, DeliverableAssignment, DeliverableStatus
from app.models.budget import BudgetEntry, BudgetType, TimeEntry
from app.models.user import User
from app.auth.middleware import require_auth, get_jwt_identity_uuid, is_admin
from backend.app.api.projects import success

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# Thresholds for risk scoring
DEADLINE_WARNING_DAYS = 14    # flag if end_date within 14 days
BUDGET_WARNING_PCT    = 80    # flag if actual >= 80% of planned
COMPLETION_RISK_PCT   = 50    # flag if completion < 50% when deadline within warning window


def _compute_project_risk(project: Project) -> dict:
    """
    Derive risk flags for a single project.
    Returns a dict with risk_level and reasons list.
    """
    today = date.today()
    reasons = []

    days_remaining = (project.end_date - today).days if project.end_date else None

    # Deadline risk
    if days_remaining is not None and days_remaining <= DEADLINE_WARNING_DAYS:
        completion = project.completion_percentage
        if completion < COMPLETION_RISK_PCT:
            reasons.append(
                f"Deadline in {days_remaining} day(s) with only {completion}% complete"
            )

    # Budget risk
    planned = project.total_planned_budget
    actual = project.total_actual_spend
    if planned > 0:
        burn_pct = (actual / planned) * 100
        if burn_pct >= BUDGET_WARNING_PCT:
            reasons.append(
                f"Budget {round(burn_pct, 1)}% consumed"
            )

    # Blocked deliverables
    blocked_count = sum(
        1 for d in project.deliverables
        if d.status == DeliverableStatus.blocked
    )
    if blocked_count:
        reasons.append(f"{blocked_count} deliverable(s) currently blocked")

    if reasons:
        risk_level = "high" if len(reasons) >= 2 else "medium"
    else:
        risk_level = "low"

    return {
        "risk_level": risk_level,
        "risk_reasons": reasons,
        "days_remaining": days_remaining,
    }


# ------------------------------------------------------------------
# GET /dashboard
# ------------------------------------------------------------------
@bp.route("", methods=["GET"])
@require_auth
def get_dashboard():
    """
    Aggregate dashboard data for the current user.
    Admins receive cross-project data. Others receive scoped data.
    """
    user_id = get_jwt_identity_uuid()
    admin = is_admin()

    # --- Determine accessible projects ---
    if admin:
        projects = Project.query.filter(
            Project.status.notin_([ProjectStatus.cancelled, ProjectStatus.completed])
        ).all()
    else:
        assigned = db.session.query(ProjectAssignment.project_id).filter_by(user_id=user_id)
        projects = Project.query.filter(
            or_(Project.created_by == user_id, Project.id.in_(assigned)),
            Project.status.notin_([ProjectStatus.cancelled, ProjectStatus.completed])
        ).all()

    # --- KPI summary ---
    total_active = len(projects)
    at_risk = []
    project_cards = []

    for p in projects:
        risk = _compute_project_risk(p)
        card = {
            "id": str(p.id),
            "name": p.name,
            "department": p.department,
            "status": p.status.value,
            "completion_percentage": p.completion_percentage,
            "end_date": p.end_date.isoformat() if p.end_date else None,
            "days_remaining": risk["days_remaining"],
            "risk_level": risk["risk_level"],
            "risk_reasons": risk["risk_reasons"],
            "total_planned_budget": float(p.total_planned_budget),
            "total_actual_spend": float(p.total_actual_spend),
        }
        project_cards.append(card)
        if risk["risk_level"] in ("medium", "high"):
            at_risk.append(card)

    # --- Overall deliverable completion ---
    all_deliverable_ids = [d.id for p in projects for d in p.deliverables]
    total_deliverables = len(all_deliverable_ids)
    completed_deliverables = sum(
        1 for p in projects for d in p.deliverables
        if d.status == DeliverableStatus.completed
    )

    # --- Resource over-allocation (based on time entries, last 30 days) ---
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    over_alloc_rows = (
        db.session.query(
            TimeEntry.user_id,
            func.sum(TimeEntry.hours).label("total_hours")
        )
        .filter(TimeEntry.entry_date >= thirty_days_ago)
        .group_by(TimeEntry.user_id)
        .having(func.sum(TimeEntry.hours) > 160)   # >160h in 30 days ≈ over-allocated
        .all()
    )

    over_allocated = []
    for row in over_alloc_rows:
        user = db.session.get(User, row.user_id)
        if user:
            over_allocated.append({
                "user_id": str(user.id),
                "full_name": user.full_name,
                "email": user.email,
                "hours_last_30_days": float(row.total_hours),
                "allocation_percentage": round((float(row.total_hours) / 160) * 100),
            })

    return success({
        "kpis": {
            "active_projects": total_active,
            "at_risk_count": len(at_risk),
            "over_allocated_members": len(over_allocated),
            "deliverable_completion_pct": (
                round((completed_deliverables / total_deliverables) * 100)
                if total_deliverables else 0
            ),
            "completed_deliverables": completed_deliverables,
            "total_deliverables": total_deliverables,
        },
        "projects": sorted(project_cards, key=lambda x: x["risk_level"] == "low"),
        "at_risk": at_risk,
        "over_allocated_members": over_allocated,
    })