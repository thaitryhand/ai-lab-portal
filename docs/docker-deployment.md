# Docker Images and Environment Variables

This document explains how environment variables flow from `.env` files into running
containers, and what to configure when deploying backend and frontend images to a
server.

## Core rule

**`.env` files are for local development and Compose interpolation — they are never
baked into Docker images.**

- Root `.env` is gitignored and listed in `.dockerignore`.
- `frontend/.env.local` is gitignored and blocked from images.
- `compose.yaml` reads root `.env` only to substitute `${VARIABLE}` placeholders.
- Containers receive configuration through explicit `environment:` entries (local)
  or platform secrets / env vars (production).

## Local full Docker stack

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local   # optional; hybrid dev only
docker compose up --build
```

| Layer | What reads `.env` | What the container sees |
| --- | --- | --- |
| Compose | Root `.env` for `${POSTGRES_HOST_PORT}`, `${DOCKER_AI_LAB_DATABASE_URL}`, etc. | Interpolated values in `compose.yaml` |
| Backend container | Nothing from disk | `AI_LAB_*` from `compose.yaml` `environment:` |
| Frontend container | Nothing from disk | `BETTER_AUTH_*`, `DATABASE_URL`, `BACKEND_INTERNAL_URL`, etc. from `environment:` |

Host-local URLs (`localhost:15432`, `127.0.0.1:18000`) must **not** be used inside
containers. Use the `DOCKER_*` variables documented in `.env.example`.

## Backend image (`backend/Dockerfile`)

**Build:**

```bash
docker build -f backend/Dockerfile -t ai-lab-portal-backend .
```

**Required runtime environment variables** (prefix `AI_LAB_`):

| Variable | Purpose |
| --- | --- |
| `AI_LAB_ENVIRONMENT` | `development`, `staging`, or `production` |
| `AI_LAB_DATABASE_URL` | SQLAlchemy Postgres URL (service hostname in deploy) |
| `AI_LAB_REDIS_URL` | Redis URL |
| `AI_LAB_ADMIN_BOUNDARY_SECRET` | Shared secret with frontend (`ADMIN_BOUNDARY_SECRET`) |
| `AI_LAB_LLM_OPENAI_API_KEY` | OpenAI API key for AI Blog Agent generation tasks; may be empty only when AI generation is intentionally disabled locally |

Optional: `AI_LAB_APP_NAME`, `AI_LAB_SERVICE_NAME`, `AI_LAB_LLM_MODEL`.

`backend/app/settings.py` loads root `.env` only when that file exists in the
process working directory (typical for host-local runs from repo root). Inside a
container there is no `.env` file — settings come from the environment only.

**Smoke check:**

```bash
docker run --rm \
  -e AI_LAB_ENVIRONMENT=development \
  -e AI_LAB_DATABASE_URL=postgresql+psycopg://user:pass@postgres:5432/db \
  -e AI_LAB_REDIS_URL=redis://redis:6379/0 \
  -e AI_LAB_ADMIN_BOUNDARY_SECRET=replace-with-shared-server-secret-at-least-32-random-characters \
  ai-lab-portal-backend:latest \
  python -c "from backend.app.settings import Settings; print(Settings().environment)"
```

## Frontend images (`frontend/Dockerfile`)

Two build targets:

| Target | Use case | Command |
| --- | --- | --- |
| `development` | `compose.yaml` local full stack (`next dev`) | Default for Compose |
| `production` | Server deploy (`next build` + `next start`) | `docker build --target production` |

**Development (Compose):**

```yaml
build:
  context: .
  dockerfile: frontend/Dockerfile
  target: development
```

Runtime env is injected at container start (same vars as `compose.yaml` `frontend.environment`).

**Production build:**

```bash
docker build -f frontend/Dockerfile \
  --target production \
  --build-arg NEXT_PUBLIC_SITE_URL=https://your-domain.example \
  -t ai-lab-portal-frontend:prod .
```

**Required runtime environment variables** (no prefix):

| Variable | Purpose |
| --- | --- |
| `BETTER_AUTH_SECRET` | Auth signing secret (≥ 32 chars) |
| `BETTER_AUTH_URL` | Public URL of the frontend app |
| `BETTER_AUTH_TRUSTED_ORIGINS` | Comma-separated allowed origins |
| `DATABASE_URL` / `AUTH_DATABASE_URL` | Postgres for Better Auth |
| `ADMIN_BOUNDARY_SECRET` | Must match `AI_LAB_ADMIN_BOUNDARY_SECRET` |
| `BACKEND_INTERNAL_URL` | Internal FastAPI URL (e.g. `http://backend:8000`) |

Optional: `BETTER_AUTH_API_KEY`, `NEXT_PUBLIC_SITE_URL` (also supported as build-arg for static inlining).

**Run production image:**

```bash
docker run --rm -p 3000:3000 \
  -e BETTER_AUTH_SECRET=... \
  -e BETTER_AUTH_URL=https://your-domain.example \
  -e BETTER_AUTH_TRUSTED_ORIGINS=https://your-domain.example \
  -e DATABASE_URL=postgresql://... \
  -e AUTH_DATABASE_URL=postgresql://... \
  -e ADMIN_BOUNDARY_SECRET=... \
  -e BACKEND_INTERNAL_URL=http://backend:8000 \
  ai-lab-portal-frontend:prod
```

On Kubernetes, ECS, Fly.io, etc., map the same names from secrets / config maps —
do not mount `.env` into the container unless you intentionally manage secrets that way.

## Verification scripts

### Container environment smoke

From repo root after `docker compose up --build -d`:

```bash
bash scripts/docker-env-smoke.sh
```

This checks that backend and frontend containers see the expected variables and that
health endpoints respond.

### Deployment HTTP smoke

After any production-like deployment is up, run:

```bash
python scripts/deploy_smoke.py \
  --backend-url http://127.0.0.1:18000 \
  --frontend-url http://127.0.0.1:13000
```

For a real server, replace both URLs with the deployed origins. The smoke script
checks:

- backend `/health` returns JSON with `status: ok`
- frontend `/` responds without a server error
- frontend `/admin/login` responds without a server error

## Deploy checklist

1. Build images in CI (`backend/Dockerfile`, `frontend/Dockerfile --target production`).
2. Push to your registry.
3. Set all required env vars on the platform (never rely on files inside the image).
4. Run Alembic migrations before or during backend rollout (`compose.yaml` backend command shows the pattern).
5. Ensure `ADMIN_BOUNDARY_SECRET` and `AI_LAB_ADMIN_BOUNDARY_SECRET` match.
6. Use internal service DNS for `BACKEND_INTERNAL_URL`, `AI_LAB_DATABASE_URL`, and Postgres URLs.
7. Set `BETTER_AUTH_URL` and `BETTER_AUTH_TRUSTED_ORIGINS` to the public HTTPS origin.
8. Set `AI_LAB_LLM_OPENAI_API_KEY` for worker-backed AI generation flows, or explicitly accept that generation endpoints will fail until it is configured.
9. Run `python scripts/deploy_smoke.py` and inspect container logs before opening traffic.

## Rollback checklist

1. Stop new traffic or disable the release at the reverse proxy/load balancer if available.
2. Redeploy the previous image tag or revert the deployment commit.
3. Do **not** roll back database migrations blindly; first check whether the migration is backward-compatible or whether a data restore is required.
4. Re-run `python scripts/deploy_smoke.py` against the rolled-back stack.
5. Record the incident and any missing automation as Harness backlog.

## Known local blocker

Docker Desktop must be running before Compose or E2E deployment smoke can start
Postgres/Redis. If `docker compose ps` cannot connect to the Docker engine,
non-Docker checks can still pass but deployment/E2E smoke is environment-blocked.
