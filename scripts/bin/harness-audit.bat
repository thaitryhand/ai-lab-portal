@echo off
REM Companion audit commands for the prebuilt Harness CLI.
REM
REM Usage:
REM   scripts\bin\harness-audit.bat traces    — Audit all trace records for completeness
REM   scripts\bin\harness-audit.bat matrix    — Audit proof matrix for missing evidence
REM   scripts\bin\harness-audit.bat help      — Show this help
REM
REM The prebuilt harness-cli.exe cannot be extended with new subcommands.
REM These wrappers delegate to the Python audit scripts so the workflow
REM stays CLI-like instead of switching to "python scripts/trace_quality.py".

setlocal enabledelayedexpansion
set REPO_ROOT=%~dp0..\..
set PYTHON=python
set SUB=%1

if /I "%SUB%"=="traces" goto :traces
if /I "%SUB%"=="matrix" goto :matrix
if /I "%SUB%"=="help" goto :help
if "%SUB%"=="" goto :help

echo Unknown subcommand: %SUB%
echo Run "scripts\bin\harness-audit help" for usage.
exit /b 1

:traces
%PYTHON% "%REPO_ROOT%\scripts\trace_quality.py"
exit /b %ERRORLEVEL%

:matrix
%PYTHON% "%REPO_ROOT%\scripts\proof_matrix_gaps.py"
exit /b %ERRORLEVEL%

:help
echo Harness audit companion commands
echo.
echo Usage:
echo   scripts\bin\harness-audit traces    Audit trace completeness
echo   scripts\bin\harness-audit matrix    Audit proof matrix gaps
echo.
echo These are lightweight wrappers around the Python audit scripts.
echo See scripts/README.md and scripts/trace_quality.py for details.
exit /b 0
