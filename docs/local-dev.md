# Local Development Quickstart

Use this page when running the AI Lab Portal on the host machine with Docker
Compose for Postgres and Redis.

## Host ports (from `compose.yaml` / `.env.example`)

| Service | Host port | Notes |
| --- | --- | --- |
| Postgres | `15432` | Mapped from container `5432` |
| Redis | `16379` | Mapped from container `6379` |
| Backend API | `18000` | FastAPI when run via compose |
| Frontend | `13000` | Next.js when run via compose |
| E2E (Playwright) | `13100` | Set `E2E_PORT` when `3000`/`13000` collide |

## Environment files

| File | Purpose |
| --- | --- |
| Root `.env` | Docker Compose variable interpolation (ports, Docker-internal URLs, shared secrets) |
| `backend/.env` | Backend `AI_LAB_*` settings for local dev (settings.py loads this by explicit path) |
| `frontend/.env` | Better Auth, Next.js public URLs, frontend `DATABASE_URL` |

**Rule:** Host-machine commands use `localhost:15432` (Postgres) and
`localhost:16379` (Redis). In-container services use `postgres:5432` and
`redis:6379` via `DOCKER_*` variables in `.env.example`.

## Common commands

```bash
# Start infrastructure
docker compose up -d postgres redis

# Backend migrations (from repo root; reads root .env)
python -m alembic -c backend/alembic.ini upgrade head

# Frontend (from frontend/)
npm run dev

# E2E (from frontend/; uses E2E_PORT when set)
E2E_PORT=13100 npm run test:e2e
```

If migrations fail with connection refused, confirm root `.env`
`AI_LAB_DATABASE_URL` uses port **15432**, not `5432`.

## E2E preflight (backlog #13)

Playwright starts a local web server and expects Postgres on host port **15432**.
If Docker Desktop is stopped, E2E fails before any test runs.

Blog agent golden-path E2E (`US-086`) uses deterministic fake LLM responses
(`AI_LAB_LLM_E2E_FAKE=true` in `frontend/playwright.config.ts`) — no OpenAI key required.

### Seed a published post via agent pipeline (US-087)

```bash
# Terminal 1 — API with fake LLM (no OpenAI key)
set AI_LAB_LLM_E2E_FAKE=true
set AI_LAB_DATABASE_URL=postgresql+psycopg://ai_lab:ai_lab_dev_password@localhost:15432/ai_lab_portal
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 18000

# Terminal 2 — seed script
python scripts/seed_blog_agent_pipeline.py
```

For real OpenAI dogfood (manual QA), use `python scripts/dogfood_blog_agent.py` with a
Celery worker and `AI_LAB_LLM_OPENAI_API_KEY` set (do not set `AI_LAB_LLM_E2E_FAKE`).

```bash
# From repo root — automated preflight (starts infra, waits for Postgres, migrates)
scripts/e2e-preflight.sh
# Windows (Git Bash): scripts/e2e-preflight.bat

# Then run E2E from frontend/
cd frontend && CI=1 E2E_PORT=13100 npm run test:e2e
```

Symptom: `webServer` timeout or Postgres connection refused in Playwright logs.
Fix: start Docker Desktop, then re-run `scripts/e2e-preflight.sh`.

## E2E secret alignment (backlog #14)

When the Docker **backend** service is already running on port `18000`, Playwright
may hit it with a different `ADMIN_BOUNDARY_SECRET` than the E2E web server uses.
That produces false admin-auth failures unrelated to the code under test.

Recommended local workflow:

```bash
# Stop compose app services so Playwright owns backend + frontend secrets
docker compose stop backend frontend worker

# Run E2E with CI=1 so Playwright starts an isolated stack (from frontend/)
cd frontend && CI=1 E2E_PORT=13100 npm run test:e2e
```

If you intentionally test against the Docker platform stack, align secrets in
root `.env` and `frontend/.env` before running E2E.

## Verified (local)

With Docker Postgres on host port `15432`:

- `python -m alembic -c backend/alembic.ini upgrade head` from repo root succeeds using
  root `.env` only (no `AI_LAB_DATABASE_URL` override).
- `npm run test:e2e` from `frontend/` reaches FastAPI on `18000` and Postgres on
  `15432` via Playwright config defaults.

## Frontend pre-commit hooks

After `npm install` in `frontend/`, git uses repo-root `.husky/pre-commit` to run
`lint-staged`, `tsc --noEmit`, and `npm run build` before each commit.

If hooks are missing on an existing clone, run once from repo root:

```bash
git config core.hooksPath .husky
# or: cd frontend && npm run prepare
```

## Harness verification

```bash
python scripts/trace_quality.py
scripts/bin/harness-cli story verify US-XXX
scripts/bin/harness-cli query matrix
git status --short   # requires a git worktree
```

### Harness hygiene (2026-06-06)

- `python scripts/trace_quality.py`: run after trace backfill; expect **0 core gaps**.
- `python scripts/proof_matrix_gaps.py`: **83 stories**, no actionable missing proof.
- Harness backlog #1–#12 → **implemented**; #13–#15 track recurring E2E/env friction.
- MVP 5 real Apify provider remains blocked on human budget/terms gate.
