CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE system_role AS ENUM (
    'admin',
    'project_manager',
    'team_member',
    'stakeholder'
);

CREATE TYPE project_status AS ENUM (
    'draft',
    'active',
    'at_risk',
    'delayed',
    'completed',
    'cancelled'
);

CREATE TYPE project_role AS ENUM (
    'lead',
    'contributor',
    'reviewer',
    'observer'
);

CREATE TYPE deliverable_status AS ENUM (
    'not_started',
    'in_progress',
    'blocked',
    'in_review',
    'completed',
    'cancelled'
);

CREATE TYPE dependency_type AS ENUM (
    'finish_to_start',
    'start_to_start',
    'finish_to_finish',
    'start_to_finish'
);

CREATE TYPE budget_type AS ENUM (
    'planned',
    'actual'
);


-- ============================================================
-- USERS
-- Core authentication and authorization identity.
-- system_role controls what the user can do across the app.
-- ============================================================

CREATE TABLE users (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    system_role     system_role  NOT NULL DEFAULT 'team_member',
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role  ON users(system_role);

COMMENT ON TABLE  users             IS 'Authentication identities and system-level roles.';
COMMENT ON COLUMN users.system_role IS 'admin | project_manager | team_member | stakeholder';
COMMENT ON COLUMN users.is_active   IS 'Soft-delete flag — deactivated users cannot log in.';


-- ============================================================
-- PROJECTS
-- Top-level container for all work at ACME.
-- Status is stored for fast dashboard reads; updated by
-- backend business logic whenever deliverables change.
-- ============================================================

CREATE TABLE projects (
    id          UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255)   NOT NULL,
    description TEXT,
    department  VARCHAR(100),
    status      project_status NOT NULL DEFAULT 'draft',
    start_date  DATE           NOT NULL,
    end_date    DATE           NOT NULL,
    created_by  UUID           NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),

    CONSTRAINT end_after_start CHECK (end_date > start_date)
);

CREATE INDEX idx_projects_status     ON projects(status);
CREATE INDEX idx_projects_created_by ON projects(created_by);
CREATE INDEX idx_projects_end_date   ON projects(end_date);

COMMENT ON TABLE  projects        IS 'Top-level project containers.';
COMMENT ON COLUMN projects.status IS 'Stored for fast dashboard reads; updated by backend business logic.';


-- ============================================================
-- PROJECT ASSIGNMENTS
-- Who is on which project, and in what project-level role.
-- project_role is distinct from system_role on users:
-- a team_member in the system can be a lead on one project.
-- ============================================================

CREATE TABLE project_assignments (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id   UUID         NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id      UUID         NOT NULL REFERENCES users(id)    ON DELETE CASCADE,
    project_role project_role NOT NULL DEFAULT 'contributor',
    assigned_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_project_user UNIQUE (project_id, user_id)
);

CREATE INDEX idx_proj_assign_project ON project_assignments(project_id);
CREATE INDEX idx_proj_assign_user    ON project_assignments(user_id);

COMMENT ON TABLE  project_assignments              IS 'Many-to-many: users <-> projects with a project-scoped role.';
COMMENT ON COLUMN project_assignments.project_role IS 'Role within this project, independent of system_role.';


-- ============================================================
-- DELIVERABLES
-- Work items within a project. Self-referencing parent_id
-- enables hierarchy: epic -> story -> task.
-- Index on parent_id is critical — hierarchy queries are frequent.
-- ============================================================

CREATE TABLE deliverables (
    id          UUID               PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID               NOT NULL REFERENCES projects(id)    ON DELETE CASCADE,
    parent_id   UUID               REFERENCES deliverables(id)         ON DELETE SET NULL,
    title       VARCHAR(255)       NOT NULL,
    description TEXT,
    status      deliverable_status NOT NULL DEFAULT 'not_started',
    due_date    DATE,
    sort_order  INTEGER            NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ        NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ        NOT NULL DEFAULT NOW(),

    CONSTRAINT no_self_parent CHECK (id != parent_id)
);

CREATE INDEX idx_deliverables_project  ON deliverables(project_id);
CREATE INDEX idx_deliverables_parent   ON deliverables(parent_id);
CREATE INDEX idx_deliverables_status   ON deliverables(status);
CREATE INDEX idx_deliverables_due_date ON deliverables(due_date);

COMMENT ON TABLE  deliverables            IS 'Work items; self-referencing for hierarchical grouping.';
COMMENT ON COLUMN deliverables.parent_id  IS 'Nullable. NULL = top-level deliverable within the project.';
COMMENT ON COLUMN deliverables.sort_order IS 'Client-controlled ordering within a sibling group.';


-- ============================================================
-- DEPENDENCIES
-- Directed dependency graph between deliverables.
-- from_deliverable must progress before to_deliverable can.
-- dependency_type follows standard PM notation.
-- ============================================================

CREATE TABLE dependencies (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    from_deliverable_id UUID            NOT NULL REFERENCES deliverables(id) ON DELETE CASCADE,
    to_deliverable_id   UUID            NOT NULL REFERENCES deliverables(id) ON DELETE CASCADE,
    dependency_type     dependency_type NOT NULL DEFAULT 'finish_to_start',
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_dependency      UNIQUE (from_deliverable_id, to_deliverable_id),
    CONSTRAINT no_self_dependency CHECK  (from_deliverable_id != to_deliverable_id)
);

CREATE INDEX idx_dependencies_from ON dependencies(from_deliverable_id);
CREATE INDEX idx_dependencies_to   ON dependencies(to_deliverable_id);

COMMENT ON TABLE  dependencies                     IS 'Directed dependency graph between deliverables.';
COMMENT ON COLUMN dependencies.from_deliverable_id IS 'Blocker — this deliverable must complete first.';
COMMENT ON COLUMN dependencies.to_deliverable_id   IS 'Blocked — this deliverable cannot proceed yet.';
COMMENT ON COLUMN dependencies.dependency_type     IS 'finish_to_start is the most common; B cannot start until A finishes.';


-- ============================================================
-- BUDGET ENTRIES
-- Planned vs actual spend per project per month.
-- One planned row + one actual row per period per project.
-- period format: YYYY-MM (e.g. 2026-06)
-- ============================================================

CREATE TABLE budget_entries (
    id          UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID           NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    entry_type  budget_type    NOT NULL,
    amount      NUMERIC(12, 2) NOT NULL CHECK (amount >= 0),
    period      VARCHAR(7)     NOT NULL,
    notes       TEXT,
    created_by  UUID           NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_budget_project_type_period UNIQUE (project_id, entry_type, period)
);

CREATE INDEX idx_budget_project ON budget_entries(project_id);
CREATE INDEX idx_budget_period  ON budget_entries(period);

COMMENT ON TABLE  budget_entries        IS 'Planned vs actual spend per project per month.';
COMMENT ON COLUMN budget_entries.period IS 'YYYY-MM string, e.g. 2026-06. One planned + one actual row per period.';
COMMENT ON COLUMN budget_entries.amount IS 'Monetary amount in USD.';


-- ============================================================
-- TIME ENTRIES
-- Hours logged by a user against a deliverable.
-- Powers over-allocation detection and utilization reporting.
-- ============================================================

CREATE TABLE time_entries (
    id             UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID           NOT NULL REFERENCES users(id)        ON DELETE CASCADE,
    deliverable_id UUID           NOT NULL REFERENCES deliverables(id) ON DELETE CASCADE,
    hours          NUMERIC(5, 2)  NOT NULL CHECK (hours > 0 AND hours <= 24),
    entry_date     DATE           NOT NULL DEFAULT CURRENT_DATE,
    notes          TEXT,
    created_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_time_entries_user        ON time_entries(user_id);
CREATE INDEX idx_time_entries_deliverable ON time_entries(deliverable_id);
CREATE INDEX idx_time_entries_date        ON time_entries(entry_date);
CREATE INDEX idx_time_entries_user_date   ON time_entries(user_id, entry_date);

COMMENT ON TABLE  time_entries       IS 'Hours logged per user per deliverable. Used for utilization and over-allocation.';
COMMENT ON COLUMN time_entries.hours IS 'Hours worked in a single entry. Max 24 per entry.';


-- ============================================================
-- TRIGGERS
-- Auto-update updated_at on every row change.
-- One function, applied to each table that has updated_at.
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_deliverables_updated_at
    BEFORE UPDATE ON deliverables
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMENT ON FUNCTION set_updated_at IS 'Trigger: keeps updated_at current on any UPDATE.';