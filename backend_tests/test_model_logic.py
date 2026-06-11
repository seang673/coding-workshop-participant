import uuid
from datetime import date
from decimal import Decimal

from app.models.budget import BudgetEntry, BudgetType
from app.models.deliverable import Dependency, Deliverable, DeliverableStatus
from app.models.project import Project


def test_project_completion_percentage_ignores_cancelled_deliverables():
    project = Project(
        name="Internal Tooling",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        created_by=uuid.uuid4(),
    )
    project.deliverables = [
        Deliverable(title="D1", status=DeliverableStatus.completed),
        Deliverable(title="D2", status=DeliverableStatus.in_progress),
        Deliverable(title="D3", status=DeliverableStatus.cancelled),
        Deliverable(title="D4", status=DeliverableStatus.completed),
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
        BudgetEntry(
            entry_type=BudgetType.planned,
            amount=Decimal("1000.00"),
            period="2026-01",
            created_by=uuid.uuid4(),
        ),
        BudgetEntry(
            entry_type=BudgetType.planned,
            amount=Decimal("250.00"),
            period="2026-02",
            created_by=uuid.uuid4(),
        ),
        BudgetEntry(
            entry_type=BudgetType.actual,
            amount=Decimal("300.00"),
            period="2026-03",
            created_by=uuid.uuid4(),
        ),
    ]

    assert project.total_planned_budget == Decimal("1250.00")
    assert project.total_actual_spend == Decimal("300.00")


def test_deliverable_is_blocked_when_upstream_not_completed():
    deliverable = Deliverable(title="QA sign-off")
    upstream = Deliverable(title="Build", status=DeliverableStatus.in_progress)
    deliverable.blocked_by = [
        Dependency(from_deliverable=upstream)
    ]

    assert deliverable.is_blocked is True


def test_deliverable_not_blocked_when_all_upstream_completed():
    deliverable = Deliverable(title="Release")
    upstream_one = Deliverable(title="QA", status=DeliverableStatus.completed)
    upstream_two = Deliverable(title="Security", status=DeliverableStatus.completed)
    deliverable.blocked_by = [
        Dependency(from_deliverable=upstream_one),
        Dependency(from_deliverable=upstream_two),
    ]

    assert deliverable.is_blocked is False
