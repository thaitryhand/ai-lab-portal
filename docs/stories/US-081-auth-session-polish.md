# US-081 Auth and Session Polish

## Status

implemented

## Lane

tiny

## Intake

Retroactive — harness hygiene sync (2026-06-06).

## Product Contract

Login, register, and logout flows should be reliable and polished: correct
content types, session refresh after auth actions, and visible password toggles.

## Acceptance Criteria

1. Login and register pages match redesigned visual standard.
2. Auth forms refresh session state after successful sign-in.
3. Password fields support show/hide toggle with correct icon sizing.
4. Logout request uses correct content type and completes without error.
5. Frontend typecheck, lint, and build pass.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A |
| Integration | Auth API boundary tests remain passing |
| E2E | Auth smoke in Playwright where covered |
| Platform | N/A |
| Release | Frontend quality gate |

## Evidence

- Commit `9090406` — fix auth forms session refresh and password visibility
- Commit `092a41e` — fix logout request content type
- Commit `b31165d` — feat: polish login and register pages
- Commit `971f737` — fix(admin): resize password eye icon for better proportion
