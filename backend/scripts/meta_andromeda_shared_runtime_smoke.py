"""
Meta Andromeda shared-runtime smoke script.

Usage examples:
  python scripts/meta_andromeda_shared_runtime_smoke.py --base-url https://example.com --reviewer-token xxx
  python scripts/meta_andromeda_shared_runtime_smoke.py --base-url http://127.0.0.1:8000 --reviewer-token xxx --operator-token yyy --output-json smoke.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from typing import Any

import requests


@dataclass
class SmokeCheckResult:
    name: str
    method: str
    url: str
    ok: bool
    status_code: int | None
    detail: str


def _headers(token: str | None) -> dict[str, str]:
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _run_check(
    *,
    session: requests.Session,
    name: str,
    method: str,
    url: str,
    token: str | None,
    timeout: float,
    expected_status: int = 200,
    assert_json_path: tuple[str, ...] | None = None,
) -> SmokeCheckResult:
    try:
        response = session.request(method=method, url=url, headers=_headers(token), timeout=timeout)
        ok = response.status_code == expected_status
        detail = f"expected {expected_status}, got {response.status_code}"
        if ok and assert_json_path:
            payload: Any = response.json()
            current = payload
            for key in assert_json_path:
                if not isinstance(current, dict) or key not in current:
                    ok = False
                    detail = f"missing json path: {'/'.join(assert_json_path)}"
                    break
                current = current[key]
            if ok:
                detail = f"json path present: {'/'.join(assert_json_path)}"
        return SmokeCheckResult(
            name=name,
            method=method,
            url=url,
            ok=ok,
            status_code=response.status_code,
            detail=detail,
        )
    except Exception as exc:
        return SmokeCheckResult(
            name=name,
            method=method,
            url=url,
            ok=False,
            status_code=None,
            detail=str(exc),
        )


def build_checks(base_url: str, reviewer_token: str | None, operator_token: str | None, timeout: float) -> list[SmokeCheckResult]:
    session = requests.Session()
    base = base_url.rstrip("/")

    checks: list[SmokeCheckResult] = []
    checks.append(
        _run_check(
            session=session,
            name="global_health",
            method="GET",
            url=f"{base}/health",
            token=None,
            timeout=timeout,
            expected_status=200,
            assert_json_path=("checks", "meta_andromeda"),
        )
    )

    if reviewer_token:
        checks.extend(
            [
                _run_check(
                    session=session,
                    name="reviewer_ping",
                    method="GET",
                    url=f"{base}/api/meta-andromeda/ping",
                    token=reviewer_token,
                    timeout=timeout,
                    expected_status=200,
                    assert_json_path=("module",),
                ),
                _run_check(
                    session=session,
                    name="reviewer_overview",
                    method="GET",
                    url=f"{base}/api/meta-andromeda/overview",
                    token=reviewer_token,
                    timeout=timeout,
                    expected_status=200,
                    assert_json_path=("summary",),
                ),
                _run_check(
                    session=session,
                    name="reviewer_runtime_health",
                    method="GET",
                    url=f"{base}/api/meta-andromeda/runtime/health",
                    token=reviewer_token,
                    timeout=timeout,
                    expected_status=200,
                    assert_json_path=("checks", "storage"),
                ),
                _run_check(
                    session=session,
                    name="reviewer_review_queue",
                    method="GET",
                    url=f"{base}/api/meta-andromeda/review-queue",
                    token=reviewer_token,
                    timeout=timeout,
                    expected_status=200,
                    assert_json_path=("summary",),
                ),
            ]
        )

    operator = operator_token or reviewer_token
    if operator:
        checks.extend(
            [
                _run_check(
                    session=session,
                    name="operator_monitoring",
                    method="GET",
                    url=f"{base}/api/meta-andromeda/monitoring/summary",
                    token=operator,
                    timeout=timeout,
                    expected_status=200,
                    assert_json_path=("worker_host",),
                ),
                _run_check(
                    session=session,
                    name="operator_release_overview",
                    method="GET",
                    url=f"{base}/api/meta-andromeda/release/overview",
                    token=operator,
                    timeout=timeout,
                    expected_status=200,
                    assert_json_path=("current_production",),
                ),
            ]
        )

    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Meta Andromeda shared-runtime smoke checks.")
    parser.add_argument("--base-url", required=True, help="Backend base URL, for example https://example.com")
    parser.add_argument("--reviewer-token", help="Bearer token for reviewer-level checks")
    parser.add_argument("--operator-token", help="Bearer token for operator-level checks")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds")
    parser.add_argument("--output-json", help="Optional file path to write structured JSON results")
    args = parser.parse_args()

    results = build_checks(
        base_url=args.base_url,
        reviewer_token=args.reviewer_token,
        operator_token=args.operator_token,
        timeout=args.timeout,
    )

    passed = 0
    for result in results:
        status_label = "PASS" if result.ok else "FAIL"
        print(f"[{status_label}] {result.name} -> {result.detail}")
        if result.ok:
            passed += 1

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "base_url": args.base_url,
                    "passed": passed,
                    "total": len(results),
                    "results": [asdict(item) for item in results],
                },
                fh,
                ensure_ascii=False,
                indent=2,
            )

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
