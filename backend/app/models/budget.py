import enum
from app import db


class BudgetType(enum.Enum):
    planned = "planned"
    actual  = "actual"


class BudgetEntry(db.Model):
    __tablename__ = "budget_entries"

    id          = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    project_id  = db.Column(db.UUID(as_uuid=True), db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    entry_type  = db.Column(db.Enum(BudgetType), nullable=False)
    amount      = db.Column(db.Numeric(12, 2), nullable=False)
    period      = db.Column(db.String(7), nullable=False)   # 'YYYY-MM'
    notes       = db.Column(db.Text)
    created_by  = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at  = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint("project_id", "entry_type", "period", name="uq_budget_project_type_period"),
    )

    project          = db.relationship("Project", back_populates="budget_entries")
    created_by_user  = db.relationship("User",    back_populates="budget_entries")

    def __repr__(self):
        return f"<BudgetEntry project={self.project_id} {self.entry_type.value} {self.period} ${self.amount}>"


class TimeEntry(db.Model):
    __tablename__ = "time_entries"

    id             = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    user_id        = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id",        ondelete="CASCADE"), nullable=False)
    deliverable_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("deliverables.id", ondelete="CASCADE"), nullable=False)
    hours          = db.Column(db.Numeric(5, 2), nullable=False)
    entry_date     = db.Column(db.Date, nullable=False, server_default=db.func.current_date())
    notes          = db.Column(db.Text)
    created_at     = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    user        = db.relationship("User",        back_populates="time_entries")
    deliverable = db.relationship("Deliverable", back_populates="time_entries")

    def __repr__(self):
        return f"<TimeEntry user={self.user_id} {self.hours}h on {self.entry_date}>"