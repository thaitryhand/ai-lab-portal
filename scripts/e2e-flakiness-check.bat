@echo off
REM E2E flakiness detection pre-commit script (Windows)
REM Checks for known flaky patterns in Playwright test files

setlocal

set "PROJECT_ROOT=%~dp0.."
set "E2E_DIR=%PROJECT_ROOT%\frontend\tests\e2e"
set "EXIT_CODE=0"

echo 🔍 Checking E2E tests for flakiness patterns...

if not exist "%E2E_DIR%" (
    echo ✅ No E2E tests directory found - skipping flakiness check
    exit /b 0
)

REM Pattern 1: waitForTimeout calls (flaky hard waits)
echo   Checking for waitForTimeout^(^) calls...
findstr /s /m /c:"waitForTimeout" "%E2E_DIR%\*.ts" "%E2E_DIR%\*.js" >nul 2>&1
if %errorlevel% equ 0 (
    echo ❌ Found waitForTimeout^(^) calls ^(use waitForSelector instead^):
    findstr /s /n /c:"waitForTimeout" "%E2E_DIR%\*.ts" "%E2E_DIR%\*.js" 2>nul | more /e +5
    set "EXIT_CODE=1"
)

REM Pattern 2: page.waitFor with numeric timeout
echo   Checking for numeric waitFor patterns...
findstr /s /m /r /c:"page\.waitFor([0-9]" "%E2E_DIR%\*.ts" "%E2E_DIR%\*.js" >nul 2>&1
if %errorlevel% equ 0 (
    echo ❌ Found numeric waitFor^(^) calls ^(use waitForSelector instead^):
    findstr /s /n /r /c:"page\.waitFor([0-9]" "%E2E_DIR%\*.ts" "%E2E_DIR%\*.js" 2>nul | more /e +5
    set "EXIT_CODE=1"
)

REM Pattern 3: Sleep or delay patterns
echo   Checking for sleep/delay patterns...
findstr /s /m /c:"sleep" /c:"delay" "%E2E_DIR%\*.ts" "%E2E_DIR%\*.js" >nul 2>&1
if %errorlevel% equ 0 (
    echo ❌ Found sleep/delay patterns ^(use proper wait conditions^):
    findstr /s /n /c:"sleep" /c:"delay" "%E2E_DIR%\*.ts" "%E2E_DIR%\*.js" 2>nul | more /e +5
    set "EXIT_CODE=1"
)

if "%EXIT_CODE%" == "0" (
    echo ✅ No E2E flakiness patterns detected
) else (
    echo.
    echo 💡 Common fixes:
    echo   - Replace waitForTimeout^(^) with waitForSelector^(^) or waitForLoadState^(^)
    echo   - Add missing 'await' before page methods
    echo   - Use element selectors instead of numeric delays
    echo   - Increase timeouts to at least 5000ms for CI environments
)

exit /b %EXIT_CODE%