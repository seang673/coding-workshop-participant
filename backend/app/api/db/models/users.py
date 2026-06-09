import enum
from app import db


class SystemRole(enum.Enum):
    admin           = "admin"
    project_manager = "project_manager"
    team_member     = "team_member"
    stakeholder     = "stakeholder"

class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    email         = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name     = db.Column(db.String(255), nullable=False)
    system_role   = db.Column(db.Enum(SystemRole), nullable=False, default=SystemRole.team_member)
    is_active     = db.Column(db.Boolean, nullable=False, default=True)
    created_at    = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at    = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    # Relationships
    created_projects       = db.relationship("Project", back_populates="creator", foreign_keys="Project.created_by")
    project_assignments    = db.relationship("ProjectAssignment", back_populates="user")
    deliverable_assignments = db.relationship("DeliverableAssignment", back_populates="user")
    time_entries           = db.relationship("TimeEntry", back_populates="user")
    budget_entries         = db.relationship("BudgetEntry", back_populates="created_by_user")

    def __repr__(self):
        return f"<User {self.email} [{self.system_role.value}]>"

    @property
    def is_admin(self):
        return self.system_role == SystemRole.admin

    @property
    def is_project_manager(self):
        return self.system_role in (SystemRole.admin, SystemRole.project_manager)