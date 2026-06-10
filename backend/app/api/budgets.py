from flask import Blueprint, request
from sqlalchemy import func
import re

from app import db
from app.models.budget import BudgetEntry, BudgetType
from app.models.project import Project
from app.models.user import SystemRole
from app.auth.middleware import require_auth, require_role, get_jwt_identity_uuid, is_admin
from app.api.helpers import success, created, error, not_found, forbidden

bp = Blueprint("budgets", __name__, url_prefix="/projects/<uuid:project_id>/budget")

PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")  # YYYY-MM


def serialize_entry(e: BudgetEntry) -> dict:
    return {
        "id": str(e.id),
        "project_id": str(e.project_id),
        "entry_type": e.entry_type.value,
        "amount": float(e.amount),
        "period": e.period,
        "notes": e.notes,
        "created_by": str(e.created_by),
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


def _check_project_access(project_id, user_id):
    p = db.session.get(Project, project_id)
    if not p:
        return None, not_found("Project")
    if not is_admin():
        assigned = {str(a.user_id) for a in p.assignments}
        if str(user_id) != str(p.created_by) and str(user_id) not in assigned:
            return None, forbidden()
    return p, None


# ------------------------------------------------------------------
# GET /projects/<id>/budget
# ------------------------------------------------------------------
@bp.route("", methods=["GET"])
@require_auth
def get_budget_summary(project_id):
    """
    Return budget summary + all entries for a project.
    Includes planned vs actual per period and totals.
    """
    user_id = get_jwt_identity_uuid()
    _, err = _check_project_access(project_id, user_id)
    if err:
        return err

    entries = BudgetEntry.query.filter_by(project_id=project_id).order_by(
        BudgetEntry.period, BudgetEntry.entry_type
    ).all()

    # Aggregate totals
    totals = (
        db.session.query(BudgetEntry.entry_type, func.sum(BudgetEntry.amount))
        .filter_by(project_id=project_id)
        .group_by(BudgetEntry.entry_type)
        .all()
    )
    total_map = {t.value: float(a) for t, a in totals}
    planned = total_map.get("planned", 0.0)
    actual = total_map.get("actual", 0.0)

    # Periods breakdown
    periods = {}
    for e in entries:
        if e.period not in periods:
            periods[e.period] = {"planned": None, "actual": None}
        periods[e.period][e.entry_type.value] = float(e.amount)

    return success({
        "summary": {
            "total_planned": planned,
            "total_actual": actual,
            "burn_percentage": round((actual / planned * 100), 1) if planned > 0 else None,
            "remaining": round(planned - actual, 2),
        },
        "by_period": [
            {"period": k, **v} for k, v in sorted(periods.items())
        ],
        "entries": [serialize_entry(e) for e in entries],
    })


# ------------------------------------------------------------------
# POST /projects/<id>/budget
# ------------------------------------------------------------------
@bp.route("", methods=["POST"])
@require_role(SystemRole.admin, SystemRole.project_manager)
def create_budget_entry(project_id):
    """
    Add or update a budget entry for a project period.
    Body: { entry_type, amount, period, notes? }
    If a planned/actual entry for that period already exists, it is updated.
    """
    user_id = get_jwt_identity_uuid()
    _, err = _check_project_access(project_id, user_id)
    if err:
        return err

    data = request.get_json(silent=True) or {}
    missing = [f for f in ("entry_type", "amount", "period") if not data.get(f)]
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}")

    try:
        entry_type = BudgetType(data["entry_type"])
    except ValueError:
        return error(f"entry_type must be 'planned' or 'actual'")

    try:
        amount = float(data["amount"])
        if amount < 0:
            raise ValueError
    except (ValueError, TypeError):
        return error("amount must be a non-negative number")

    period = data["period"]
    if not PERIOD_RE.match(period):
        return error("period must be in YYYY-MM format (e.g. 2026-06)")

    # Upsert: update if exists for this project/type/period
    existing = BudgetEntry.query.filter_by(
        project_id=project_id,
        entry_type=entry_type,
        period=period,
    ).first()

    if existing:
        existing.amount = amount
        existing.notes = data.get("notes", existing.notes)
        db.session.commit()
        return success(serialize_entry(existing), "Budget entry updated")

    entry = BudgetEntry(
        project_id=project_id,
        entry_type=entry_type,
        amount=amount,
        period=period,
        notes=data.get("notes"),
        created_by=user_id,
    )
    db.session.add(entry)
    db.session.commit()
    return created(serialize_entry(entry), "Budget entry created")


# ------------------------------------------------------------------
# DELETE /projects/<id>/budget/<entry_id>
# ------------------------------------------------------------------
@bp.route("/<uuid:entry_id>", methods=["DELETE"])
@require_role(SystemRole.admin, SystemRole.project_manager)
def delete_budget_entry(project_id, entry_id):
    entry = db.session.get(BudgetEntry, entry_id)
    if not entry or str(entry.project_id) != str(project_id):
        return not_found("Budget entry")
    db.session.delete(entry)
    db.session.commit()
    return success(message="Budget entry deleted")