import enum
from app import db


class ProjectStatus(enum.Enum):
    draft     = "draft"
    active    = "active"
    at_risk   = "at_risk"
    delayed   = "delayed"
    completed = "completed"
    cancelled = "cancelled"


class ProjectRole(enum.Enum):
    lead        = "lead"
    contributor = "contributor"
    reviewer    = "reviewer"
    observer    = "observer"


class Project(db.Model):
    __tablename__ = "projects"

    id          = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    name        = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    department  = db.Column(db.String(100))
    status      = db.Column(db.Enum(ProjectStatus), nullable=False, default=ProjectStatus.draft)
    start_date  = db.Column(db.Date, nullable=False)
    end_date    = db.Column(db.Date, nullable=False)
    created_by  = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    created_at  = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at  = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    # Relationships
    creator      = db.relationship("User", back_populates="created_projects", foreign_keys=[created_by])
    assignments  = db.relationship("ProjectAssignment", back_populates="project", cascade="all, delete-orphan")
    deliverables = db.relationship("Deliverable", back_populates="project", cascade="all, delete-orphan")
    budget_entries = db.relationship("BudgetEntry", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project '{self.name}' [{self.status.value}]>"

    @property
    def completion_percentage(self):
        """Percentage of non-cancelled deliverables that are completed."""
        eligible = [d for d in self.deliverables if d.status.value != "cancelled"]
        if not eligible:
            return 0
        done = sum(1 for d in eligible if d.status.value == "completed")
        return round((done / len(eligible)) * 100)

    @property
    def total_planned_budget(self):
        from app.models.budget import BudgetType
        return sum(
            e.amount for e in self.budget_entries
            if e.entry_type == BudgetType.planned
        )

    @property
    def total_actual_spend(self):
        from app.models.budget import BudgetType
        return sum(
            e.amount for e in self.budget_entries
            if e.entry_type == BudgetType.actual
        )


class ProjectAssignment(db.Model):
    __tablename__ = "project_assignments"

    id           = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    project_id   = db.Column(db.UUID(as_uuid=True), db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id      = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id",    ondelete="CASCADE"), nullable=False)
    project_role = db.Column(db.Enum(ProjectRole), nullable=False, default=ProjectRole.contributor)
    assigned_at  = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint("project_id", "user_id", name="uq_project_user"),
    )

    # Relationships
    project = db.relationship("Project", back_populates="assignments")
    user    = db.relationship("User",    back_populates="project_assignments")

    def __repr__(self):
        return f"<ProjectAssignment project={self.project_id} user={self.user_id} role={self.project_role.value}>"