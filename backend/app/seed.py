"""
Seed data — populates the database with realistic ACME Inc. sample data.

Call `run()` inside an active app context (see `backend/seed.py` for the local
CLI entrypoint, and `app/function.py`'s `_migrate` action for the Lambda
one-time migration entrypoint).

Idempotent: running it twice will not duplicate data (checks for existing
users first).
"""
from datetime import date, timedelta

from app import db
from app.models.user import User, SystemRole
from app.models.project import Project, ProjectAssignment, ProjectStatus, ProjectRole
from app.models.deliverable import (
    Deliverable, DeliverableAssignment, DeliverableStatus, Dependency, DependencyType
)
from app.models.budget import BudgetEntry, BudgetType, TimeEntry
from app.auth.utils import hash_password

PASSWORD = "Password123"   # all seed users share this password


def run():
    """Seed the database with sample users, projects, deliverables, and budgets."""
    # Idempotency check
    if User.query.filter_by(email="admin@acme.com").first():
        print("Seed data already exists. Skipping.")
        return

    print("Seeding database...")

    # ── Users ───────────────────────────────────────────────────
    admin = User(
        email="admin@acme.com", full_name="Alex Admin",
        password_hash=hash_password(PASSWORD), system_role=SystemRole.admin,
    )
    pm1 = User(
        email="pm1@acme.com", full_name="Priya Mendez",
        password_hash=hash_password(PASSWORD), system_role=SystemRole.project_manager,
    )
    pm2 = User(
        email="pm2@acme.com", full_name="Jordan Lee",
        password_hash=hash_password(PASSWORD), system_role=SystemRole.project_manager,
    )
    dev1 = User(
        email="dev1@acme.com", full_name="Sam Chen",
        password_hash=hash_password(PASSWORD), system_role=SystemRole.team_member,
    )
    dev2 = User(
        email="dev2@acme.com", full_name="Anika Patel",
        password_hash=hash_password(PASSWORD), system_role=SystemRole.team_member,
    )
    dev3 = User(
        email="dev3@acme.com", full_name="Marcus Torres",
        password_hash=hash_password(PASSWORD), system_role=SystemRole.team_member,
    )
    stakeholder = User(
        email="exec@acme.com", full_name="Casey Rivera",
        password_hash=hash_password(PASSWORD), system_role=SystemRole.stakeholder,
    )

    db.session.add_all([admin, pm1, pm2, dev1, dev2, dev3, stakeholder])
    db.session.flush()

    today = date.today()

    # ── Project 1: Platform Migration (On Track) ─────────────────
    p1 = Project(
        name="Platform Migration", department="Engineering",
        status=ProjectStatus.active,
        start_date=today - timedelta(days=60),
        end_date=today + timedelta(days=45),
        created_by=pm1.id,
    )
    db.session.add(p1)
    db.session.flush()

    db.session.add_all([
        ProjectAssignment(project_id=p1.id, user_id=pm1.id,  project_role=ProjectRole.lead),
        ProjectAssignment(project_id=p1.id, user_id=dev1.id, project_role=ProjectRole.contributor),
        ProjectAssignment(project_id=p1.id, user_id=dev2.id, project_role=ProjectRole.contributor),
    ])

    p1_d1 = Deliverable(project_id=p1.id, title="Infrastructure audit",       status=DeliverableStatus.completed,   due_date=today - timedelta(days=40), sort_order=1)
    p1_d2 = Deliverable(project_id=p1.id, title="Cloud environment setup",    status=DeliverableStatus.completed,   due_date=today - timedelta(days=20), sort_order=2)
    p1_d3 = Deliverable(project_id=p1.id, title="Data migration scripts",     status=DeliverableStatus.in_progress, due_date=today + timedelta(days=10), sort_order=3)
    p1_d4 = Deliverable(project_id=p1.id, title="UAT and sign-off",           status=DeliverableStatus.not_started, due_date=today + timedelta(days=35), sort_order=4)
    p1_d5 = Deliverable(project_id=p1.id, title="Go-live and cutover",        status=DeliverableStatus.not_started, due_date=today + timedelta(days=44), sort_order=5)
    db.session.add_all([p1_d1, p1_d2, p1_d3, p1_d4, p1_d5])
    db.session.flush()

    db.session.add_all([
        DeliverableAssignment(deliverable_id=p1_d3.id, user_id=dev1.id),
        DeliverableAssignment(deliverable_id=p1_d3.id, user_id=dev2.id),
        DeliverableAssignment(deliverable_id=p1_d4.id, user_id=pm1.id),
        Dependency(from_deliverable_id=p1_d2.id, to_deliverable_id=p1_d3.id, dependency_type=DependencyType.finish_to_start),
        Dependency(from_deliverable_id=p1_d3.id, to_deliverable_id=p1_d4.id, dependency_type=DependencyType.finish_to_start),
        Dependency(from_deliverable_id=p1_d4.id, to_deliverable_id=p1_d5.id, dependency_type=DependencyType.finish_to_start),
    ])

    # Budget: Platform Migration
    for month_offset, planned, actual in [(-2, 40000, 38000), (-1, 50000, 47000), (0, 55000, 30000)]:
        period = (today.replace(day=1) + timedelta(days=32 * month_offset)).strftime("%Y-%m")
        db.session.add_all([
            BudgetEntry(project_id=p1.id, entry_type=BudgetType.planned, amount=planned, period=period, created_by=pm1.id),
            BudgetEntry(project_id=p1.id, entry_type=BudgetType.actual,  amount=actual,  period=period, created_by=pm1.id),
        ])

    # ── Project 2: CRM Rollout (At Risk) ─────────────────────────
    p2 = Project(
        name="CRM Rollout", department="Sales",
        status=ProjectStatus.at_risk,
        start_date=today - timedelta(days=45),
        end_date=today + timedelta(days=8),
        created_by=pm2.id,
    )
    db.session.add(p2)
    db.session.flush()

    db.session.add_all([
        ProjectAssignment(project_id=p2.id, user_id=pm2.id,  project_role=ProjectRole.lead),
        ProjectAssignment(project_id=p2.id, user_id=dev2.id, project_role=ProjectRole.contributor),
        ProjectAssignment(project_id=p2.id, user_id=dev3.id, project_role=ProjectRole.contributor),
    ])

    p2_d1 = Deliverable(project_id=p2.id, title="Requirements gathering",    status=DeliverableStatus.completed,   due_date=today - timedelta(days=30), sort_order=1)
    p2_d2 = Deliverable(project_id=p2.id, title="CRM configuration",         status=DeliverableStatus.in_progress, due_date=today + timedelta(days=2),  sort_order=2)
    p2_d3 = Deliverable(project_id=p2.id, title="Data import and cleanup",   status=DeliverableStatus.blocked,     due_date=today + timedelta(days=4),  sort_order=3)
    p2_d4 = Deliverable(project_id=p2.id, title="Sales team training",       status=DeliverableStatus.not_started, due_date=today + timedelta(days=7),  sort_order=4)
    p2_d5 = Deliverable(project_id=p2.id, title="Launch",                    status=DeliverableStatus.not_started, due_date=today + timedelta(days=8),  sort_order=5)
    db.session.add_all([p2_d1, p2_d2, p2_d3, p2_d4, p2_d5])
    db.session.flush()

    db.session.add_all([
        DeliverableAssignment(deliverable_id=p2_d2.id, user_id=dev3.id),
        DeliverableAssignment(deliverable_id=p2_d3.id, user_id=dev2.id),
        Dependency(from_deliverable_id=p2_d2.id, to_deliverable_id=p2_d3.id, dependency_type=DependencyType.finish_to_start),
        Dependency(from_deliverable_id=p2_d3.id, to_deliverable_id=p2_d4.id, dependency_type=DependencyType.finish_to_start),
    ])

    for month_offset, planned, actual in [(-1, 30000, 29000), (0, 35000, 32000)]:
        period = (today.replace(day=1) + timedelta(days=32 * month_offset)).strftime("%Y-%m")
        db.session.add_all([
            BudgetEntry(project_id=p2.id, entry_type=BudgetType.planned, amount=planned, period=period, created_by=pm2.id),
            BudgetEntry(project_id=p2.id, entry_type=BudgetType.actual,  amount=actual,  period=period, created_by=pm2.id),
        ])

    # ── Project 3: Data Warehouse Rebuild (Delayed) ───────────────
    p3 = Project(
        name="Data Warehouse Rebuild", department="Analytics",
        status=ProjectStatus.delayed,
        start_date=today - timedelta(days=90),
        end_date=today + timedelta(days=5),
        created_by=pm1.id,
    )
    db.session.add(p3)
    db.session.flush()

    db.session.add_all([
        ProjectAssignment(project_id=p3.id, user_id=pm1.id,  project_role=ProjectRole.lead),
        ProjectAssignment(project_id=p3.id, user_id=dev1.id, project_role=ProjectRole.contributor),
        ProjectAssignment(project_id=p3.id, user_id=dev3.id, project_role=ProjectRole.contributor),
    ])

    p3_d1 = Deliverable(project_id=p3.id, title="Schema design",             status=DeliverableStatus.completed,   due_date=today - timedelta(days=60), sort_order=1)
    p3_d2 = Deliverable(project_id=p3.id, title="ETL pipeline build",        status=DeliverableStatus.in_progress, due_date=today - timedelta(days=10), sort_order=2)
    p3_d3 = Deliverable(project_id=p3.id, title="Historical data backfill",  status=DeliverableStatus.blocked,     due_date=today + timedelta(days=1),  sort_order=3)
    p3_d4 = Deliverable(project_id=p3.id, title="Dashboard connections",     status=DeliverableStatus.not_started, due_date=today + timedelta(days=4),  sort_order=4)
    db.session.add_all([p3_d1, p3_d2, p3_d3, p3_d4])
    db.session.flush()

    db.session.add_all([
        DeliverableAssignment(deliverable_id=p3_d2.id, user_id=dev1.id),
        DeliverableAssignment(deliverable_id=p3_d3.id, user_id=dev3.id),
        Dependency(from_deliverable_id=p3_d2.id, to_deliverable_id=p3_d3.id, dependency_type=DependencyType.finish_to_start),
        Dependency(from_deliverable_id=p3_d3.id, to_deliverable_id=p3_d4.id, dependency_type=DependencyType.finish_to_start),
    ])

    for month_offset, planned, actual in [(-2, 20000, 19500), (-1, 25000, 26000), (0, 25000, 22000)]:
        period = (today.replace(day=1) + timedelta(days=32 * month_offset)).strftime("%Y-%m")
        db.session.add_all([
            BudgetEntry(project_id=p3.id, entry_type=BudgetType.planned, amount=planned, period=period, created_by=pm1.id),
            BudgetEntry(project_id=p3.id, entry_type=BudgetType.actual,  amount=actual,  period=period, created_by=pm1.id),
        ])

    # ── Project 4: HR Self-Service Portal (On Track, nearly done) ─
    p4 = Project(
        name="HR Self-Service Portal", department="HR",
        status=ProjectStatus.active,
        start_date=today - timedelta(days=120),
        end_date=today + timedelta(days=14),
        created_by=pm2.id,
    )
    db.session.add(p4)
    db.session.flush()

    db.session.add_all([
        ProjectAssignment(project_id=p4.id, user_id=pm2.id,  project_role=ProjectRole.lead),
        ProjectAssignment(project_id=p4.id, user_id=dev2.id, project_role=ProjectRole.contributor),
    ])

    p4_d1 = Deliverable(project_id=p4.id, title="UX design and prototyping", status=DeliverableStatus.completed,   due_date=today - timedelta(days=80), sort_order=1)
    p4_d2 = Deliverable(project_id=p4.id, title="Backend API",               status=DeliverableStatus.completed,   due_date=today - timedelta(days=40), sort_order=2)
    p4_d3 = Deliverable(project_id=p4.id, title="Frontend build",            status=DeliverableStatus.completed,   due_date=today - timedelta(days=14), sort_order=3)
    p4_d4 = Deliverable(project_id=p4.id, title="QA and testing",            status=DeliverableStatus.in_review,   due_date=today + timedelta(days=7),  sort_order=4)
    p4_d5 = Deliverable(project_id=p4.id, title="Deployment to production",  status=DeliverableStatus.not_started, due_date=today + timedelta(days=13), sort_order=5)
    db.session.add_all([p4_d1, p4_d2, p4_d3, p4_d4, p4_d5])
    db.session.flush()

    db.session.add(DeliverableAssignment(deliverable_id=p4_d4.id, user_id=dev2.id))

    # ── Time entries (last 30 days — dev2 is over-allocated) ──────
    time_entries = []
    for i in range(25):
        d = today - timedelta(days=i)
        # dev1 — normal load ~6h/day
        time_entries.append(TimeEntry(user_id=dev1.id, deliverable_id=p1_d3.id, hours=6, entry_date=d))
        # dev2 — over-allocated: on p1 + p2 + p4
        time_entries.append(TimeEntry(user_id=dev2.id, deliverable_id=p1_d3.id, hours=5, entry_date=d))
        time_entries.append(TimeEntry(user_id=dev2.id, deliverable_id=p2_d2.id, hours=4, entry_date=d))
        # dev3 — moderate load
        time_entries.append(TimeEntry(user_id=dev3.id, deliverable_id=p3_d2.id, hours=7, entry_date=d))

    db.session.add_all(time_entries)
    db.session.commit()

    print("\n✓ Seed complete. Accounts created:")
    print("  admin@acme.com        — Admin")
    print("  pm1@acme.com          — Project Manager (Priya Mendez)")
    print("  pm2@acme.com          — Project Manager (Jordan Lee)")
    print("  dev1@acme.com         — Team Member (Sam Chen)")
    print("  dev2@acme.com         — Team Member (Anika Patel) [over-allocated]")
    print("  dev3@acme.com         — Team Member (Marcus Torres)")
    print("  exec@acme.com         — Stakeholder")
    print(f"\n  All passwords: {PASSWORD}")
    print("\n  Projects seeded: 4")
    print(f"  Deliverables seeded: {5+5+4+5}")
    print(f"  Time entries seeded: {len(time_entries)}")
