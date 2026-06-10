# Backend Test Starter Pack

This folder contains lightweight tests that validate core backend behavior without needing a fully seeded database.

## What these tests cover

- App bootstrap and `/health` response contract
- Auth endpoint validation behavior (missing/invalid payloads)
- API response envelope helpers (`success`, `error`, `paginate`)
- Core model business logic properties:
  - project completion percentage
  - planned vs actual budget totals
  - deliverable blocking logic

## Run

From the project root:

```bash
pytest backend_tests -q
```

If `pytest` is missing:

```bash
pip install pytest
```

## Notes

- Tests set `DATABASE_URL` to SQLite in-memory for isolation.
- These are intentionally small tests intended to reveal backend behavior quickly.
