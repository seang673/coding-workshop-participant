import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.models.budget import BudgetType
from app.models.deliverable import Deliverable, DeliverableStatus
from app.models.project import Project


class _D:
    def __init__(self, status):
        self.status = status


class _BudgetEntry:
    def __init__(self, entry_type, amount):
        self.entry_type = entry_type
        self.amount = amount


def test_project_completion_percentage_ignores_cancelled_deliverables():
    project = Project(
        name="Internal Tooling",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        created_by=uuid.uuid4(),
    )
    project.deliverables = [
        _D(DeliverableStatus.completed),
        _D(DeliverableStatus.in_progress),
        _D(DeliverableStatus.cancelled),
        _D(DeliverableStatus.completed),
    ]

    assert project.completion_percentage == 67


def test_project_budget_totals_sum_by_entry_type():
    project = Project(
        name="Migration",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 6, 1),
        created_by=uuid.uuid4(),
    )
    project.budget_entries = [
        _BudgetEntry(BudgetType.planned, Decimal("1000.00")),
        _BudgetEntry(BudgetType.planned, Decimal("250.00")),
        _BudgetEntry(BudgetType.actual, Decimal("300.00")),
    ]

    assert project.total_planned_budget == Decimal("1250.00")
    assert project.total_actual_spend == Decimal("300.00")


def test_deliverable_is_blocked_when_upstream_not_completed():
    deliverable = Deliverable(title="QA sign-off")
    deliverable.blocked_by = [
        SimpleNamespace(from_deliverable=SimpleNamespace(status=DeliverableStatus.in_progress))
    ]

    assert deliverable.is_blocked is True


def test_deliverable_not_blocked_when_all_upstream_completed():
    deliverable = Deliverable(title="Release")
    deliverable.blocked_by = [
        SimpleNamespace(from_deliverable=SimpleNamespace(status=DeliverableStatus.completed)),
        SimpleNamespace(from_deliverable=SimpleNamespace(status=DeliverableStatus.completed)),
    ]

    assert deliverable.is_blocked is False
