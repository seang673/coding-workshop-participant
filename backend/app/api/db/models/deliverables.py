import enum
from app import db


class DeliverableStatus(enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    blocked     = "blocked"
    in_review   = "in_review"
    completed   = "completed"
    cancelled   = "cancelled"


class DependencyType(enum.Enum):
    finish_to_start  = "finish_to_start"   # most common
    start_to_start   = "start_to_start"
    finish_to_finish = "finish_to_finish"
    start_to_finish  = "start_to_finish"


class Deliverable(db.Model):
    __tablename__ = "deliverables"

    id          = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    project_id  = db.Column(db.UUID(as_uuid=True), db.ForeignKey("projects.id",      ondelete="CASCADE"), nullable=False)
    parent_id   = db.Column(db.UUID(as_uuid=True), db.ForeignKey("deliverables.id",  ondelete="SET NULL"), nullable=True)
    title       = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status      = db.Column(db.Enum(DeliverableStatus), nullable=False, default=DeliverableStatus.not_started)
    due_date    = db.Column(db.Date, nullable=True)
    sort_order  = db.Column(db.Integer, nullable=False, default=0)
    created_at  = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at  = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    # Self-referential hierarchy
    children = db.relationship(
        "Deliverable",
        backref=db.backref("parent", remote_side="Deliverable.id"),
        lazy="dynamic"
    )

    # Relationships
    project     = db.relationship("Project", back_populates="deliverables")
    assignments = db.relationship("DeliverableAssignment", back_populates="deliverable", cascade="all, delete-orphan")
    time_entries = db.relationship("TimeEntry", back_populates="deliverable", cascade="all, delete-orphan")

    # Dependencies: deliverables this one blocks, and deliverables blocking this one
    blocking = db.relationship(
        "Dependency",
        foreign_keys="Dependency.from_deliverable_id",
        back_populates="from_deliverable",
        cascade="all, delete-orphan"
    )
    blocked_by = db.relationship(
        "Dependency",
        foreign_keys="Dependency.to_deliverable_id",
        back_populates="to_deliverable",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Deliverable '{self.title}' [{self.status.value}]>"

    @property
    def is_blocked(self):
        """True if any upstream dependency is not yet completed."""
        return any(
            dep.from_deliverable.status != DeliverableStatus.completed
            for dep in self.blocked_by
        )


class DeliverableAssignment(db.Model):
    __tablename__ = "deliverable_assignments"

    id             = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    deliverable_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("deliverables.id", ondelete="CASCADE"), nullable=False)
    user_id        = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id",        ondelete="CASCADE"), nullable=False)
    assigned_at    = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint("deliverable_id", "user_id", name="uq_deliverable_user"),
    )

    deliverable = db.relationship("Deliverable", back_populates="assignments")
    user        = db.relationship("User", back_populates="deliverable_assignments")


class Dependency(db.Model):
    __tablename__ = "dependencies"

    id                  = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    from_deliverable_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("deliverables.id", ondelete="CASCADE"), nullable=False)
    to_deliverable_id   = db.Column(db.UUID(as_uuid=True), db.ForeignKey("deliverables.id", ondelete="CASCADE"), nullable=False)
    dependency_type     = db.Column(db.Enum(DependencyType), nullable=False, default=DependencyType.finish_to_start)
    created_at          = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint("from_deliverable_id", "to_deliverable_id", name="uq_dependency"),
        db.CheckConstraint("from_deliverable_id != to_deliverable_id", name="no_self_dependency"),
    )

    from_deliverable = db.relationship("Deliverable", foreign_keys=[from_deliverable_id], back_populates="blocking")
    to_deliverable   = db.relationship("Deliverable", foreign_keys=[to_deliverable_id],   back_populates="blocked_by")

    def __repr__(self):
        return f"<Dependency {self.from_deliverable_id} --[{self.dependency_type.value}]--> {self.to_deliverable_id}>"