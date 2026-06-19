#!/bin/bash
# E2E flakiness detection pre-commit script
# Checks for known flaky patterns in Playwright test files

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
E2E_DIR="$PROJECT_ROOT/frontend/tests/e2e"
EXIT_CODE=0

echo "🔍 Checking E2E tests for flakiness patterns..."

if [ ! -d "$E2E_DIR" ]; then
    echo "✅ No E2E tests directory found - skipping flakiness check"
    exit 0
fi

# Pattern 1: waitForTimeout calls (flaky hard waits)
echo "  Checking for waitForTimeout() calls..."
if grep -r "waitForTimeout" "$E2E_DIR" --include="*.ts" --include="*.js" >/dev/null 2>&1; then
    echo "❌ Found waitForTimeout() calls (use waitForSelector instead):"
    grep -rn "waitForTimeout" "$E2E_DIR" --include="*.ts" --include="*.js" | head -5
    EXIT_CODE=1
fi

# Pattern 2: Missing await before Playwright methods
echo "  Checking for missing await keywords..."
if grep -r "page\.\w\+(" "$E2E_DIR" --include="*.ts" --include="*.js" | grep -v "await page\." >/dev/null 2>&1; then
    echo "❌ Found potential missing await before page methods:"
    grep -rn "page\.\w\+(" "$E2E_DIR" --include="*.ts" --include="*.js" | grep -v "await page\." | head -5
    EXIT_CODE=1
fi

# Pattern 3: page.waitFor with numeric timeout (use waitForSelector instead)
echo "  Checking for numeric waitFor patterns..."
if grep -r "page\.waitFor([0-9]" "$E2E_DIR" --include="*.ts" --include="*.js" >/dev/null 2>&1; then
    echo "❌ Found numeric waitFor() calls (use waitForSelector instead):"
    grep -rn "page\.waitFor([0-9]" "$E2E_DIR" --include="*.ts" --include="*.js" | head -5
    EXIT_CODE=1
fi

# Pattern 4: Very short timeouts (less than 1000ms)
echo "  Checking for overly short timeouts..."
if grep -r "timeout.*: *[1-9][0-9]\{0,2\}[^0-9]" "$E2E_DIR" --include="*.ts" --include="*.js" >/dev/null 2>&1; then
    echo "❌ Found potentially too-short timeouts (< 1000ms):"
    grep -rn "timeout.*: *[1-9][0-9]\{0,2\}[^0-9]" "$E2E_DIR" --include="*.ts" --include="*.js" | head -5
    EXIT_CODE=1
fi

# Pattern 5: Sleep or delay patterns
echo "  Checking for sleep/delay patterns..."
if grep -r "sleep\|delay" "$E2E_DIR" --include="*.ts" --include="*.js" >/dev/null 2>&1; then
    echo "❌ Found sleep/delay patterns (use proper wait conditions):"
    grep -rn "sleep\|delay" "$E2E_DIR" --include="*.ts" --include="*.js" | head -5
    EXIT_CODE=1
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ No E2E flakiness patterns detected"
else
    echo ""
    echo "💡 Common fixes:"
    echo "  - Replace waitForTimeout() with waitForSelector() or waitForLoadState()"
    echo "  - Add missing 'await' before page methods"
    echo "  - Use element selectors instead of numeric delays"
    echo "  - Increase timeouts to at least 5000ms for CI environments"
fi

exit $EXIT_CODE