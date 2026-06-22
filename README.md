# FastAPI + MySQL on EKS

A production-grade web application built with FastAPI and MySQL, designed to run on AWS EKS. The app exposes a UI and JSON API for safely querying a user database through predefined, parametrized filters. It is built with a GitOps deployment model (ArgoCD), automated CI (GitHub Actions), and first-class observability (Prometheus + Grafana).

This repository follows a phased delivery plan. The current phase is **Phase 0: Local Development**. See [`planning/PROJECT_PLAN.md`](planning/PROJECT_PLAN.md) for the full roadmap.

---

## Architecture Overview

```
GitHub Repo
  └── GitHub Actions (CI)
        test → build → push image to ECR → update k8s manifest
              └── ArgoCD (CD)
                    watches repo, syncs to EKS
                          └── EKS Cluster
                                ├── FastAPI Deployment + Service + Ingress
                                │     └── RDS MySQL (private subnet)
                                └── Prometheus + Grafana
```

**Stack at a glance:**

| Layer | Technology |
|---|---|
| Application | FastAPI (Python 3.12) |
| Database | MySQL 8 (local: Docker, prod: AWS RDS) |
| ORM | SQLAlchemy 2 (sync, pymysql driver) |
| Templating | Jinja2 |
| Metrics | prometheus-fastapi-instrumentator |
| Container | Docker (multi-stage, non-root) |
| Orchestration | AWS EKS |
| GitOps | ArgoCD |
| CI | GitHub Actions |
| Observability | Prometheus + Grafana (kube-prometheus-stack) |

---

## Repository Structure

```
.
├── app/
│   ├── main.py               # FastAPI app, routes
│   ├── db.py                 # SQLAlchemy engine + session
│   ├── models.py             # User ORM model
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── queries.py            # Predefined, parametrized query functions
│   ├── seed.py               # Demo data seeding on first boot
│   ├── templates/
│   │   └── index.html        # Jinja2 query UI
│   ├── requirements.txt
│   ├── Dockerfile            # Multi-stage, non-root
│   └── tests/
│       ├── conftest.py       # SQLite in-memory test fixtures
│       ├── test_health.py
│       └── test_queries.py
├── planning/
│   ├── PROJECT_PLAN.md       # Full phased delivery plan
│   └── local_test.md         # Phase 0 task brief
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Local Development (Phase 0)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### Quickstart

```bash
# 1. Clone the repo
git clone <repo-url>
cd EKS_fastapi

# 2. Create your local environment file
cp .env.example .env

# 3. Start the app and database
docker-compose up --build
```

On first startup, the database is created and seeded automatically with ~25 demo users. No manual SQL steps needed.

### Endpoints

| Endpoint | Description |
|---|---|
| `http://localhost:8000/` | Query UI (browser) |
| `http://localhost:8000/health` | Health check + DB connectivity |
| `http://localhost:8000/metrics` | Prometheus metrics |
| `http://localhost:8000/api/query` | JSON query API |

### Stopping and resetting

```bash
# Stop containers
docker-compose down

# Stop and wipe the database volume (full reset)
docker-compose down -v
```

---

## Environment Variables

Copy `.env.example` to `.env` and adjust values as needed.

| Variable | Description | Default |
|---|---|---|
| `DB_HOST` | MySQL host | `db` |
| `DB_PORT` | MySQL port | `3306` |
| `DB_USER` | App database user | `app` |
| `DB_PASSWORD` | App database password | `changeme` |
| `DB_NAME` | Database name | `appdb` |
| `DB_ROOT_PASSWORD` | MySQL root password (Docker only) | `rootchangeme` |

Never commit a real `.env` file — it is listed in `.gitignore`.

---

## Query API Reference

### `GET /api/query`

Returns a JSON list of users based on the selected filter.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `filter_type` | string | Required. One of: `all`, `status`, `date_range`, `country`, `name_search` |
| `status` | string | `active` or `inactive`. Used when `filter_type=status` |
| `country` | string | Country name (exact match). Used when `filter_type=country` |
| `name_search` | string | Partial name match (case-insensitive LIKE). Used when `filter_type=name_search` |
| `date_from` | ISO date | Start of signup range e.g. `2025-01-01`. Used when `filter_type=date_range` |
| `date_to` | ISO date | End of signup range e.g. `2025-12-31`. Used when `filter_type=date_range` |
| `page` | integer | Page number (default: `1`, 20 results per page) |

**Example requests:**

```bash
# All users, page 1
curl "http://localhost:8000/api/query?filter_type=all"

# Active users only
curl "http://localhost:8000/api/query?filter_type=status&status=active"

# Users from Japan
curl "http://localhost:8000/api/query?filter_type=country&country=Japan"

# Name search
curl "http://localhost:8000/api/query?filter_type=name_search&name_search=alice"

# Signed up in 2025 Q1
curl "http://localhost:8000/api/query?filter_type=date_range&date_from=2025-01-01&date_to=2025-03-31"
```

**Example response:**

```json
{
  "results": [
    {
      "id": 1,
      "name": "Alice Johnson",
      "email": "alice.johnson@example.com",
      "status": "active",
      "country": "United Kingdom",
      "created_at": "2025-08-06T00:00:00"
    }
  ]
}
```

### `GET /health`

Returns HTTP 200 when the app is running and connected to the database, or HTTP 503 if the DB is unreachable.

```json
{ "status": "ok", "db": true }
```

### `GET /metrics`

Returns Prometheus-formatted metrics. Used by Prometheus scraping in Phase 6.

---

## Running Tests

Tests run against an SQLite in-memory database — no Docker or running MySQL required.

```bash
cd app
pip install -r requirements.txt
pytest tests/ -v
```

Test coverage includes:

- `test_health.py` — `/health` returns 200 with correct shape
- `test_queries.py` — all filter types, response shape, edge cases

---

## Security Design

The user-facing query interface is the highest-risk component of this app. The following controls are in place:

- **No raw SQL input from the UI.** All queries are predefined functions in `queries.py` with SQLAlchemy parametrized bindings. Users select filters from dropdowns — they cannot type arbitrary SQL.
- **LIKE queries use parametrized values**, not string concatenation.
- **DB credentials are environment variables only** — never hardcoded, never committed.
- The Dockerfile runs as a **non-root user** in the final stage.
- In production, the RDS instance sits in a **private subnet** with no public access.

---

## Delivery Phases

| Phase | Status | Description |
|---|---|---|
| 0 | In progress | Local dev: FastAPI + MySQL via Docker Compose |
| 1 | Planned | AWS networking + RDS MySQL |
| 2 | Planned | EKS cluster provisioning |
| 3 | Planned | Manual deploy to EKS, validate end-to-end |
| 4 | Planned | ArgoCD GitOps |
| 5 | Planned | GitHub Actions CI |
| 6 | Planned | Prometheus + Grafana monitoring |
| 7 | Planned | Production hardening (TLS, HPA, network policies) |

See [`planning/PROJECT_PLAN.md`](planning/PROJECT_PLAN.md) for the full checklist and architecture decisions.
