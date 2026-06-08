#!/usr/bin/env bash
# TurboPack + Kysely compatibility regression check
#
# Next.js turbopack and Kysely have known dependency-resolution interactions:
# - serverExternalPackages: ["kysely"] in next.config.ts tells Next.js to keep
#   Kysely as an external server package during builds.
# - Version bumps to either Next.js or Kysely may silently break turbopack dev
#   mode (next dev --turbo) or the production build.
#
# This script runs the standard next build (webpack) and warns about turbopack
# mode, so agents can catch regressions before committing.

set -euo pipefail

echo "=== TurboPack + Kysely compatibility check ==="

# Determine frontend directory relative to this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

if [ ! -d "$FRONTEND_DIR" ]; then
  echo "❌ frontend/ directory not found at $FRONTEND_DIR"
  exit 1
fi

cd "$FRONTEND_DIR"

# 1. Verify next build passes (webpack bundler — validates Kysely resolves)
echo ""
echo "[1/2] Running next build (webpack)..."
if npm run build 2>&1; then
  echo "✅ next build passed"
else
  echo "❌ next build failed — Kysely or Next.js dependency may be incompatible"
  exit 1
fi

# 2. Warn about turbopack dev mode risk
echo ""
echo "[2/2] Turbopack dev mode check..."
NEXT_VERSION=$(node -e "console.log(require('next/package.json').version || 'unknown')" 2>/dev/null || echo "unknown")
KYSELY_VERSION=$(node -e "console.log(require('kysely/package.json').version || 'unknown')" 2>/dev/null || echo "unknown")

echo "  Next.js version : $NEXT_VERSION"
echo "  Kysely version  : $KYSELY_VERSION"
echo ""
echo "⚠️  Note: next dev --turbo may behave differently from next build."
echo "   If you upgrade Next.js or Kysely, verify dev mode manually:"
echo "     cd frontend && npm run dev"
echo ""
echo "=== Check complete ==="
