#!/usr/bin/env python3
"""Production-like deployment smoke checks for AI Lab Portal.

Run this after a Docker Compose or server deployment is up. It intentionally uses
only the Python standard library so it can run from a fresh checkout or CI image.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def request(url: str, timeout: float) -> tuple[int, str]:
    req = Request(url, headers={"User-Agent": "ai-lab-portal-deploy-smoke/1.0"})
    with urlopen(req, timeout=timeout) as response:  # noqa: S310 - operator-provided smoke URL
        body = response.read(4096).decode("utf-8", errors="replace")
        return response.status, body


def wait_for(name: str, url: str, timeout: float, deadline: float, expect_json_health: bool = False) -> CheckResult:
    end = monotonic() + deadline
    last_error = "not attempted"
    while monotonic() < end:
        try:
            status, body = request(url, timeout)
            if status >= 500:
                last_error = f"HTTP {status}"
            elif expect_json_health:
                payload = json.loads(body)
                if payload.get("status") == "ok":
                    return CheckResult(name, True, f"{url} -> HTTP {status}, status=ok")
                last_error = f"unexpected health payload: {payload!r}"
            else:
                return CheckResult(name, True, f"{url} -> HTTP {status}")
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        sleep(2)
    return CheckResult(name, False, f"{url} did not become healthy: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test a deployed AI Lab Portal stack")
    parser.add_argument("--backend-url", default="http://127.0.0.1:18000", help="Backend base URL")
    parser.add_argument("--frontend-url", default="http://127.0.0.1:13000", help="Frontend base URL")
    parser.add_argument("--deadline", type=float, default=60, help="Seconds to wait for each endpoint")
    parser.add_argument("--request-timeout", type=float, default=5, help="Per-request timeout in seconds")
    args = parser.parse_args()

    backend = args.backend_url.rstrip("/")
    frontend = args.frontend_url.rstrip("/")
    checks = [
        wait_for("backend /health", f"{backend}/health", args.request_timeout, args.deadline, expect_json_health=True),
        wait_for("frontend /", frontend, args.request_timeout, args.deadline),
        wait_for("frontend /admin/login", f"{frontend}/admin/login", args.request_timeout, args.deadline),
    ]

    for check in checks:
        marker = "ok" if check.ok else "fail"
        print(f"[{marker}] {check.name}: {check.detail}")

    if not all(check.ok for check in checks):
        return 1

    print("Deployment smoke checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
