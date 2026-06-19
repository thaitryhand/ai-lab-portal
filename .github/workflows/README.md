# CI/CD Workflows

This directory contains GitHub Actions workflows for the AI Lab Portal project.

## ci.yml - Main CI Pipeline

**Triggers:**
- Push to `main` branch
- Pull requests targeting `main` branch

**Jobs:**

### 1. `validate-harness` 
- Validates that `harness-cli.exe` exists at `scripts/bin/harness-cli.exe`
- Quick sanity check for the project's harness tooling

### 2. `backend-tests`
- **Environment:** Ubuntu with Python 3.12
- **Services:** PostgreSQL (pgvector/pg17), Redis (8-alpine)
- **Steps:**
  - Install Python dependencies via `pip install -e ".[dev]"`
  - Run database migrations with Alembic
  - Execute tests with `pytest backend/tests/`
- **Duration:** ~3-5 minutes

### 3. `frontend-quality`
- **Environment:** Ubuntu with Node.js 20
- **Steps:**
  - Install dependencies with `npm ci`
  - TypeScript type checking (`npm run typecheck`)
  - Linting with ESLint (`npm run lint`)  
  - Production build (`npm run build`)
- **Duration:** ~2-4 minutes

### 4. `frontend-unit-tests`
- **Environment:** Ubuntu with Node.js 20
- **Steps:**
  - Install dependencies with `npm ci`
  - Run component tests with Vitest (`npm run test:component`)
- **Duration:** ~1-2 minutes

### 5. `e2e-tests`
- **Trigger:** Runs on pushes to main OR PRs with `run-e2e` label
- **Environment:** Ubuntu with Node.js 20 + Python 3.12
- **Services:** Full Docker Compose stack (postgres, redis, backend, frontend)
- **Steps:**
  - Install Playwright browsers
  - Start database services via Docker Compose
  - Run migrations
  - Start backend API server
  - Start frontend development server  
  - Execute Playwright tests (`npm run test:e2e`)
  - Upload test reports as artifacts
- **Duration:** ~8-12 minutes

### 6. `docker-health-check`
- **Environment:** Ubuntu
- **Steps:**
  - Test Docker Compose services startup (postgres, redis)
  - Verify backend service builds successfully
  - No full stack deployment, just build validation
- **Duration:** ~3-5 minutes

## Environment Variables

The workflow uses test-safe environment variables from `.env.example`:
- PostgreSQL: `ai_lab_portal_test` database with `ai_lab_test` user
- Redis: Default configuration on port 6379
- No real API keys or secrets (uses fake values for testing)

## Caveats

1. **E2E Tests:** Require Docker and are resource-intensive. Only run on main branch pushes or PRs with `run-e2e` label.

2. **Windows Harness CLI:** The `harness-cli.exe` validation only checks file existence on Linux CI runners (can't execute Windows binaries).

3. **Database Migrations:** Tests run migrations but don't persist data between jobs.

4. **Playwright Reports:** Available as downloadable artifacts for 7 days when E2E tests run.

## Adding the `run-e2e` Label

To trigger E2E tests on a PR, add the `run-e2e` label in the GitHub UI:
1. Go to your PR page
2. Click "Labels" on the right sidebar  
3. Add `run-e2e` label
4. E2E tests will run on the next push to the PR branch