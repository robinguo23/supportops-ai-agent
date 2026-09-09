#!/usr/bin/env python3
import argparse
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urljoin


CONFIRMATION = "I_OWN_THIS_TARGET"
RATE_LIMIT_REQUESTS = 105
RATE_LIMIT_POLL_SECONDS = 5
RATE_LIMIT_WAIT_SECONDS = int(os.getenv("WAF_RATE_LIMIT_WAIT_SECONDS", "90"))


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
    TestCase("Untrusted security API", "/security-api", 403),
)


def request_status(url: str) -> int:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "supportops-security-regression/1.2"},
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def run_rate_limit_test(target_url: str) -> bool:
    for request_number in range(1, RATE_LIMIT_REQUESTS + 1):
        try:
            status = request_status(urljoin(target_url, "chat"))
        except (OSError, urllib.error.URLError) as error:
            print(f"FAIL Chat rate limit: request error: {error}")
            return False

        if status == 403:
            print(
                "PASS Chat rate limit: observed 403 after "
                f"{request_number} requests"
            )
            return True

        time.sleep(0.02)

    print(
        "Rate threshold reached; waiting for AWS WAF rate-based evaluation "
        f"for up to {RATE_LIMIT_WAIT_SECONDS}s."
    )

    deadline = time.monotonic() + RATE_LIMIT_WAIT_SECONDS
    polls = 0

    while time.monotonic() < deadline:
        time.sleep(RATE_LIMIT_POLL_SECONDS)
        polls += 1
        try:
            status = request_status(urljoin(target_url, "chat"))
        except (OSError, urllib.error.URLError) as error:
            print(f"FAIL Chat rate limit: polling error: {error}")
            return False

        if status == 403:
            print(
                "PASS Chat rate limit: observed 403 after threshold "
                f"and {polls} poll(s)"
            )
            return True

    print(
        "FAIL Chat rate limit: no 403 observed after threshold and "
        f"{RATE_LIMIT_WAIT_SECONDS}s of polling"
    )
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run controlled WAF regression tests against SupportOps."
    )
    parser.add_argument("--target-url", required=True)
    parser.add_argument("--confirmation", required=True)
    parser.add_argument(
        "--skip-rate-limit",
        action="store_true",
        help="Skip the rate-based rule test when running locally.",
    )
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
    total_tests = len(TEST_CASES)

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

    if not args.skip_rate_limit:
        total_tests += 1
        if not run_rate_limit_test(target_url):
            failures += 1

    print(f"Completed {total_tests} tests with {failures} failure(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
