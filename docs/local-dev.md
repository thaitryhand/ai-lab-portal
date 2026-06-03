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

### Post-MVP4 audit (2026-06-03)

- `python scripts/trace_quality.py`: **0 core gaps** (outcome/friction complete).
- Advisory only: `missing_intake` on older traces; traces #85–92 are minimal tier
  (closeout/docs slices) without Standard+ agent/actions/read/changed fields.
- `scripts/bin/harness-cli story verify US-032` … `US-046` → all pass.
- Harness backlog items #1–#9 → **implemented**; MVP 5 remains blocked (X/Twitter).
