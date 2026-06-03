#!/usr/bin/env bash
# Verify Docker Compose wiring: env vars reach containers and services respond.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> compose config"
docker compose config --quiet

echo "==> backend settings inside container (no .env file on disk)"
docker compose run --rm --no-deps backend python - <<'PY'
import os
from pathlib import Path

from backend.app.settings import Settings

assert not Path(".env").is_file(), "backend container must not ship with a .env file"
settings = Settings()
assert settings.environment in {"development", "staging", "production", "test"}
assert "postgres" in str(settings.database_url), settings.database_url
assert os.environ.get("AI_LAB_DATABASE_URL"), "AI_LAB_DATABASE_URL must be set by compose"
print("backend settings ok:", settings.environment, str(settings.database_url)[:60])
PY

echo "==> frontend env inside container"
docker compose run --rm --no-deps --entrypoint node frontend - <<'NODE'
const required = [
  "BETTER_AUTH_SECRET",
  "BETTER_AUTH_URL",
  "DATABASE_URL",
  "ADMIN_BOUNDARY_SECRET",
  "BACKEND_INTERNAL_URL",
];
for (const name of required) {
  if (!process.env[name]?.trim()) {
    throw new Error(`missing ${name} in frontend container environment`);
  }
}
if (!process.env.BACKEND_INTERNAL_URL.includes("backend")) {
  throw new Error(`BACKEND_INTERNAL_URL should use docker service DNS, got ${process.env.BACKEND_INTERNAL_URL}`);
}
console.log("frontend env ok:", process.env.BACKEND_INTERNAL_URL);
NODE

echo "==> optional live stack health (skip if services not running)"
if docker compose ps --status running 2>/dev/null | grep -q backend; then
  docker compose exec -T backend python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).read().decode())"
else
  echo "backend not running — start with: docker compose up --build -d"
fi

echo "==> all docker env smoke checks passed"
