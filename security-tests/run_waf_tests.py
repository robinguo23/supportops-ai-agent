#!/usr/bin/env python3
import argparse
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urljoin


CONFIRMATION = "I_OWN_THIS_TARGET"


@dataclass(frozen=True)
class TestCase:
    name: str
    path: str
    expected_status: int


TEST_CASES = (
    TestCase("Normal frontend health", "/health", 200),
    TestCase(
        "SQL injection",
        "/knowledge/search?query=%27%20OR%201%3D1--",
        403,
    ),
    TestCase(
        "Cross-site scripting",
        "/knowledge/search?query=%3Cscript%3Ealert(1)%3C%2Fscript%3E",
        403,
    ),
    TestCase(
        "Path traversal",
        "/knowledge/search?query=..%2F..%2Fetc%2Fpasswd",
        403,
    ),
    TestCase(
        "Known bad input",
        "/?url=http%3A%2F%2F169.254.169.254%2Flatest%2Fmeta-data",
        403,
    ),
)


def request_status(url: str) -> int:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "supportops-security-regression/1.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run controlled WAF regression tests against SupportOps."
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
    failures = 0

    for test_case in TEST_CASES:
        url = urljoin(target_url, test_case.path.lstrip("/"))

        try:
            actual_status = request_status(url)
        except (OSError, urllib.error.URLError) as error:
            print(f"FAIL {test_case.name}: request error: {error}")
            failures += 1
            continue

        passed = actual_status == test_case.expected_status
        result = "PASS" if passed else "FAIL"
        print(
            f"{result} {test_case.name}: "
            f"expected {test_case.expected_status}, got {actual_status}"
        )

        if not passed:
            failures += 1

    print(f"Completed {len(TEST_CASES)} tests with {failures} failure(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
