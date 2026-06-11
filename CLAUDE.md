# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a coding-workshop project: a project/deliverable/resource/budget tracking
platform for a fictional company "ACME Inc." (see `overview.md` for the full business
requirements). Stack:

- **Backend**: Python / Flask (`backend/app/`)
- **Database**: PostgreSQL (`backend/migrations/schema.sql`)
- **Frontend**: React + Vite + Material UI (`frontend/`)
- **Infra**: Terraform, deployed to AWS serverless (Lambda, S3, CloudFront, Aurora) or
  LocalStack for local dev (`infra/`, `bin/`)

## Commands

### Backend (Flask)

From `backend/`, using the venv at `backend/.venv` (create with
`python3 -m venv .venv && .venv/bin/pip install -r app/requirements.txt` if missing):

```sh
# Run the dev server (binds 0.0.0.0:5000)
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/coding_workshop_db \
  .venv/bin/python -m app.wsgi
```

- Local Postgres on this machine uses password `postgres123` — note this **differs**
  from the fallback default in `app/config.py` (`...postgres:password@...`), so
  `DATABASE_URL` must be set explicitly for local runs.
- First-time DB setup: create the `coding_workshop_db` database, apply
  `backend/migrations/schema.sql`, then run `python seed.py` (from `backend/`, with
  `DATABASE_URL` set) to populate realistic ACME sample data (users, projects,
  deliverables, dependencies, budgets, time entries — all seed users have password
  `Password123`). The seed script is idempotent.

### Backend tests

```sh
# From repo root
pytest backend_tests -q

# Single test file / test
pytest backend_tests/test_health_and_auth_validation.py -q
pytest backend_tests/test_model_logic.py::test_name -q
```

These tests use an in-memory SQLite DB (`conftest.py` sets `DATABASE_URL`,
`SECRET_KEY`, `JWT_SECRET_KEY` defaults) and don't require Postgres.

### Frontend (React + Vite)

```sh
cd frontend
npm install
npm run dev      # Vite dev server on port 3000
npm run build
npm run lint
```

### Full local stack (LocalStack + Terraform + both servers)

```sh
./bin/start-dev.sh
```

See `bin/README.md` for what each script under `bin/` does (`deploy-backend.sh`,
`deploy-frontend.sh`, `setup-environment.sh`, `cleanup-environment.sh`, etc.).

### Security scan (matches CI)

```sh
cd backend && .venv/bin/python -m bandit -r app -q
```

### Deploying to AWS (workshop participant environment)

```sh
./bin/setup-participant.sh        # refresh short-lived AWS creds into ENVIRONMENT.config (expire ~12-18h)
source ENVIRONMENT.config

./bin/deploy-backend.sh aws       # terraform apply + package backend/app/ as Lambda zip + update function code
./bin/deploy-frontend.sh aws      # npm run build + aws s3 sync dist/ + CloudFront invalidation
```

- If `aws sts get-caller-identity` fails with an expired-token error, re-run
  `./bin/setup-participant.sh` before deploying.
- Frontend-only changes only need `deploy-frontend.sh`; backend-only changes only
  need `deploy-backend.sh`.
- Live site is served via CloudFront (`website_url` Terraform output), e.g.
  `https://d3n0h80k1xj414.cloudfront.net`, backed by S3 bucket
  `coding-workshop-website-<participant_id>`.

## Backend Architecture

The backend is a single Flask app using the application-factory pattern
(`backend/app/__init__.py:create_app`), with Flask-SQLAlchemy, Flask-Migrate,
Flask-JWT-Extended, and Flask-CORS.

- **`app/config.py`** — `DevelopmentConfig`/`ProductionConfig`, selected via
  `FLASK_ENV` (defaults to development). DB URI from `DATABASE_URL`.
- **`app/models/`** — one file per domain area, **singular module names**
  (`user.py`, `project.py`, `deliverable.py`, `budget.py`); `budget.py` contains both
  `BudgetEntry`/`BudgetType` and `TimeEntry`. All models use UUID PKs and the schema in
  `backend/migrations/schema.sql` is the source of truth for constraints/enums/triggers.
- **`app/auth/`** — JWT auth. `routes.py` defines `/auth/*` endpoints (register, login,
  refresh, me); `middleware.py` provides `@require_auth` and `@require_role(*roles)`
  decorators plus helpers (`get_jwt_identity_uuid`, `is_admin`,
  `current_user_role`); `utils.py` handles password hashing (werkzeug PBKDF2) and
  token generation. `app/auth/__init__.py` just re-exports `bp` from `routes.py`.
- **`app/api/`** — one blueprint per resource (`projects.py`, `deliverables.py`,
  `assignments.py`, `dependencies.py`, `budgets.py`, `time_entries.py`, `users.py`,
  `dashboard.py`). `helpers.py` provides the shared response envelope
  (`success`, `created`, `error`, `not_found`, `forbidden`, `paginate`) — always import
  these from `app.api.helpers`. `app/api/__init__.py` re-exports each blueprint as
  `<name>_bp` for registration in `create_app`.
- **`app/errors.py`** — global JSON error handlers (400/401/403/404/405/409/422/500)
  registered in `create_app` so all errors return JSON, not HTML.

### Domain model & business rules

- **RBAC**: two layers — `system_role` on `User` (admin / project_manager /
  team_member / stakeholder) and `project_role` on `ProjectAssignment` (lead /
  contributor / reviewer / observer). Enforced via the `@require_role` decorator and
  `is_admin`/`is_project_manager` helpers.
- **Deliverables** are hierarchical (self-referential `parent_id`) and support
  `?tree=true` nested listing. Status changes go through a `VALID_TRANSITIONS` state
  machine in `app/api/deliverables.py`.
- **Dependencies** between deliverables form a directed graph; creation validates
  same-project, no self-reference, no duplicates, and runs a BFS cycle check
  (`app/api/dependencies.py`).
- **Budgets**: `BudgetEntry` rows are `planned`/`actual` per `(project, period)` where
  period is `YYYY-MM`; `app/api/budgets.py` upserts and computes burn percentage.
- **Time entries**: logged per user/deliverable (max 24h/day); `/reports/allocation`
  flags users over 160h in the trailing 30 days.
- **Dashboard** (`app/api/dashboard.py`) aggregates KPIs (completion %, budget burn,
  blocked deliverables, over-allocation) with results scoped by the requester's role.

### Known gaps / things to watch for

- `backend/README.md` and `infra/locals.tf` describe a generic per-service Lambda
  layout (`backend/<service>/function.py`, auto-discovered by Terraform).
  `backend/app/function.py` provides this adapter, wiring the Flask app into the
  Terraform-discovered Lambda function. `backend/app/` also contains vendored
  dependency `dist-info` folders as part of the Lambda packaging.
- An orphaned `deliverable_assignments` table exists in the live Aurora DB but is
  unused by the application — candidate for removal in a future migration.

## Frontend Architecture

React + Vite + MUI, routed with React Router v6 (`frontend/src/App.jsx`).

- **`src/theme.js`** — centralized MUI theme (`createTheme`): Indigo primary /
  Teal secondary palette, shared `shape`/`typography`/component style overrides
  (buttons, paper, app bar, table headers). Imported once into `App.jsx` and
  applied via `ThemeProvider`.
- **`src/context/AuthContext.jsx`** — auth state (current user, login/logout,
  token storage); `useAuth()` hook used throughout.
- **`src/components/Layout.jsx`** — authenticated shell: `AppBar` with desktop nav
  (`Button` + `NavLink` for active-route styling) and a mobile hamburger `Drawer`,
  wraps routed pages via `<Outlet />`. Nav links are filtered by `system_role`.
- **`src/pages/`** — one component per route: `EntryPage`, `LoginPage`,
  `RegisterPage`, `DashboardPage`, `ProjectsPage`, `ProjectDetailPage`,
  `MyTimeLogPage`, `AllocationReportPage`, `AdminUsersPage`.
- **`src/components/`** — `DeliverableTree` (recursive, hierarchical deliverable
  list with status changes, dependencies, log-time and manage actions),
  `ProjectMembersPanel`, `DeliverableFormDialog`, `LogTimeDialog`, `ConfirmDialog`.
- **`src/services/`** — one Axios-based module per API resource (`api.js` holds
  the configured client + interceptors; `projects.js`, `deliverables.js`,
  `assignments.js`, `dashboard.js`, `timeEntries.js`, `users.js`).
- **`src/utils/`** — `statusColors.js` (status/role label and color maps),
  `deliverableTransitions.js` (mirrors backend `VALID_TRANSITIONS`).
- **Responsive design**: implemented via MUI `sx` breakpoint objects
  (`{ xs, sm, md }`) — table columns hidden on narrow screens, `Layout`'s nav
  collapses into a `Drawer` below `md`, forms/cards use fluid widths. No separate
  responsive library is used.

## Code Style (from `.github/instructions/`)

- **Python** (`backend/**/*.py`): snake_case for variables/functions, CamelCase for
  classes, PEP 8, type hints on all function params/returns, docstrings on all public
  modules/classes/functions/methods.
- **React** (`frontend/**/*.{js,jsx,ts,tsx}`): camelCase for variables/functions,
  PascalCase for components/classes, Airbnb style guide, PropTypes on all components,
  JSDoc on public functions/components.
- **Terraform** (`infra/*.tf`): snake_case for resources/variables, comments on all
  resources/variables, prefer modules for reusable infra, run `terraform validate`
  before committing.
