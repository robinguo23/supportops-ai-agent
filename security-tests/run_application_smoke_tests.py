#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urljoin


CONFIRMATION = "I_OWN_THIS_TARGET"


@dataclass(frozen=True)
class TestCase:
    name: str
    method: str
    path: str
    expected_statuses: tuple[int, ...]
    body: dict | None = None


def parse_response_body(raw_body: str) -> dict | str | None:
    if not raw_body:
        return None
    try:
        return json.loads(raw_body)
    except json.JSONDecodeError:
        return raw_body


def request(target_url: str, test_case: TestCase) -> tuple[int, dict | str | None]:
    url = urljoin(target_url, test_case.path.lstrip("/"))
    body = (
        json.dumps(test_case.body).encode("utf-8")
        if test_case.body is not None
        else None
    )

    headers = {
        "Accept": "application/json, text/plain",
        "User-Agent": "supportops-application-smoke/1.0",
    }

    if body is not None:
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=test_case.method,
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw_body = response.read().decode("utf-8")
            return response.status, parse_response_body(raw_body)
    except urllib.error.HTTPError as error:
        raw_body = error.read().decode("utf-8")
        return error.code, parse_response_body(raw_body)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run safe application smoke tests against SupportOps."
    )
    parser.add_argument("--target-url", required=True)
    parser.add_argument("--confirmation", required=True)
    args = parser.parse_args()

    if args.confirmation != CONFIRMATION:
        print(
            "Refusing to run: confirm ownership with "
            f"--confirmation {CONFIRMATION}",
            file=sys.stderr,
        )
        return 2

    target_url = args.target_url.rstrip("/") + "/"
    test_cases = (
        TestCase("Backend health", "GET", "/health", (200,)),
        TestCase("Database health", "GET", "/db/health", (200,)),
        TestCase(
            "Out-of-scope chat guardrail",
            "POST",
            "/chat",
            (200,),
            {"message": "What is the weather today?"},
        ),
        TestCase(
            "Unauthenticated ticket access is denied",
            "GET",
            "/tickets",
            (401, 503),
        ),
    )

    failures = 0

    for test_case in test_cases:
        try:
            status, response_body = request(target_url, test_case)
        except (OSError, urllib.error.URLError) as error:
            print(f"FAIL {test_case.name}: request error: {error}")
            failures += 1
            continue

        passed = status in test_case.expected_statuses

        if test_case.name == "Backend health" and passed:
            passed = response_body in ("ok", {"status": "ok"})

        if test_case.name == "Database health" and passed:
            passed = isinstance(response_body, dict) and response_body.get("status") == "ok"

        if test_case.name == "Out-of-scope chat guardrail" and passed:
            passed = (
                isinstance(response_body, dict)
                and response_body.get("tool_used") == "out_of_scope_guardrail"
            )

        result = "PASS" if passed else "FAIL"
        expected = ", ".join(str(value) for value in test_case.expected_statuses)
        print(
            f"{result} {test_case.name}: "
            f"expected {expected}, got {status}"
        )

        if not passed:
            failures += 1

    print(
        f"Completed {len(test_cases)} application smoke tests with "
        f"{failures} failure(s)."
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
