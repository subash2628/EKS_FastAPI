# Instructions for Claude Code: Local FastAPI + MySQL Setup (Phase 0)

Use this as the task brief for Claude Code. Paste it in directly or reference this file.

---

## Goal

Scaffold a local development environment for the FastAPI + MySQL app described in `PROJECT_PLAN.md`. This is **Phase 0 only** — local dev via Docker Compose. No AWS, no Kubernetes yet.

## Context

- This app will eventually run on EKS with RDS MySQL, behind ArgoCD/CI, with Prometheus metrics.
- For now we only need: FastAPI app + MySQL, both running in Docker Compose, with a working UI to query the DB safely.
- Refer to `PROJECT_PLAN.md` Phase 0 checklist and Section 5 (Security Notes) before writing the query interface.

## Tasks

1. **Repo scaffold**
   Create this structure:
   ```
   app/
     main.py
     db.py
     models.py
     schemas.py
     queries.py          # predefined/parametrized query definitions
     templates/
       index.html
     requirements.txt
     Dockerfile
     tests/
       test_health.py
       test_queries.py
   docker-compose.yml
   .env.example
   .gitignore
   ```

2. **FastAPI app**
   - Use SQLAlchemy (sync, with `pymysql` driver) for the DB layer.
   - `db.py`: engine + session creation, reading connection settings from environment variables (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`).
   - `models.py`: a `User` SQLAlchemy ORM model with fields like: `id`, `name`, `email`, `status` (e.g. `active`/`inactive`), `created_at`, `country`.
   - `queries.py`: a small set of **predefined, parametrized query functions** against the `users` table, e.g.:
     - get all users (paginated)
     - filter by status (`active`/`inactive`)
     - filter by signup date range
     - filter by country
     - search by name (use `LIKE` with a parametrized value, not string concatenation)
     **Do not implement raw/free-form SQL input from the UI** — this matches the security note in `PROJECT_PLAN.md` Section 5.
   - `main.py`:
     - `/` route: serves a simple Jinja2 HTML page with a form (dropdowns/inputs) that maps to the predefined queries, displaying results in a table.
     - `/api/query` (POST or GET, your call): accepts the selected filter params, runs the corresponding parametrized query, returns JSON.
     - `/health`: returns 200 + simple JSON status, and should check DB connectivity (e.g. `SELECT 1`).
     - `/metrics`: instrument with `prometheus-fastapi-instrumentator` (even though Prometheus isn't deployed yet, wire it up now so it's ready for Phase 6).

3. **Seed data**
   - Add a small SQL seed script or a startup hook that creates the `users` table and inserts ~20-30 demo rows (varied names, emails, statuses, countries, and `created_at` dates spread over the last year) if the DB is empty, so the UI has something meaningful to filter/query immediately after `docker-compose up`.

4. **Dockerfile**
   - Multi-stage build, slim Python base image (e.g. `python:3.12-slim`).
   - Don't run as root in the final image.
   - `requirements.txt` should include at minimum: `fastapi`, `uvicorn`, `sqlalchemy`, `pymysql`, `jinja2`, `python-multipart`, `prometheus-fastapi-instrumentator`, `pytest`, `httpx`.

5. **docker-compose.yml**
   - Two services: `app` (build from `app/Dockerfile`) and `db` (official `mysql:8` image).
   - `app` depends on `db` with a healthcheck-based condition (don't just use `depends_on` without `condition: service_healthy` — MySQL takes a few seconds to be ready).
   - `db` healthcheck: `mysqladmin ping`.
   - Persist MySQL data with a named volume.
   - Map app port 8000:8000.
   - Use environment variables sourced from `.env` (create `.env.example` with placeholder values, and `.gitignore` the real `.env`).

6. **Tests**
   - `test_health.py`: hits `/health`, expects 200.
   - `test_queries.py`: hits `/api/query` with valid filter params, expects 200 and expected JSON shape.
   - Use `pytest` + `httpx` (or `TestClient` from `fastapi.testclient`).

7. **README snippet**
   - Add a short "Local Development" section (either in a new `app/README.md` or appended to the project root if a README exists) explaining:
     ```
     cp .env.example .env
     docker-compose up --build
     # App: http://localhost:8000
     # Health: http://localhost:8000/health
     # Metrics: http://localhost:8000/metrics
     ```

## Constraints / Things to avoid

- Do **not** implement raw free-form SQL query input from the UI — this is explicitly called out as the highest-risk part of the app in `PROJECT_PLAN.md`. Stick to a constrained, parametrized query builder.
- Do **not** hardcode DB credentials anywhere — always via environment variables / `.env`.
- Don't add Kubernetes, AWS, ArgoCD, or CI config yet — that's later phases. Keep this scoped to local Docker Compose only.
- Keep the Dockerfile production-reasonable from the start (multi-stage, non-root) since this same image will later be pushed to ECR and deployed to EKS — don't introduce dev-only shortcuts that will need rework later.

## Definition of done

- [ ] `docker-compose up --build` brings up both services cleanly with no manual intervention
- [ ] `/health` returns 200 and confirms DB connectivity
- [ ] `/` shows a working UI to run at least 2-3 different predefined queries against seeded demo data
- [ ] `/metrics` returns Prometheus-formatted metrics
- [ ] `pytest` passes locally
- [ ] No raw SQL string concatenation from user input anywhere in the codebase