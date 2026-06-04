# Validation

## Commands

```text
docker compose config --quiet
python -m pytest backend/tests
cd frontend && npm run typecheck && npm run lint && npm run build
scripts/bin/harness-cli.exe story verify US-024
```

## Acceptance Evidence

- 2026-06-02 US-024 local dev workflow hardening:
  - Updated `compose.yaml` to use root `.env` interpolation with safe local defaults instead of hardcoded service settings where practical.
  - Added Docker-specific variables such as `DOCKER_AI_LAB_DATABASE_URL`, `DOCKER_AI_LAB_REDIS_URL`, `DOCKER_BACKEND_INTERNAL_URL`, and `DOCKER_DATABASE_URL` so host-local env values do not conflict with container-internal URLs.
  - Updated `compose.yaml` backend env with explicit `AI_LAB_ADMIN_BOUNDARY_SECRET` mapping.
  - Updated `compose.yaml` frontend env with `ADMIN_BOUNDARY_SECRET`, `BACKEND_INTERNAL_URL`, and `NEXT_PUBLIC_SITE_URL` mappings for full Docker mode.
  - Updated root `.env.example` to document Compose interpolation variables, host-local variables, and Docker-internal variables.
  - Updated `backend/.env.example` Redis host port to `16379` for host-local dev.
  - Rewrote `docs/local-development.md` to document two supported workflows:
    - Full Docker: `docker compose up --build`.
    - Hybrid local dev: `docker compose up -d postgres redis`, local backend, local frontend.
  - Documented root `.env` vs `backend/.env` behavior, Compose `.env` interpolation semantics, and host-vs-container URLs.
  - `docker compose config --quiet` → pass.
  - `python -m pytest backend/tests` → 32 passed.
  - `cd frontend && npm run typecheck && npm run lint && npm run build` → pass.
  - `scripts/bin/harness-cli.exe story verify US-024` → pass.
- 2026-06-04 E2E proof gap closeout:
  - Docker Desktop started successfully and `docker compose up -d postgres redis` started local infrastructure.
  - `docker compose config --quiet` → pass.
  - `CI=1 E2E_PORT=13100 npm run test:e2e` from `frontend/` → 7 passed.
