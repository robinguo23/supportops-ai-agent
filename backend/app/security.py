import hmac
import os

from fastapi import Header, HTTPException


def require_admin_api_key(
    x_admin_api_key: str | None = Header(
        default=None,
        alias="X-Admin-API-Key",
    ),
) -> None:
    expected_api_key = os.getenv("ADMIN_API_KEY", "").strip()

    if not expected_api_key:
        raise HTTPException(
            status_code=503,
            detail="Admin ticket access is not configured.",
        )

    if not x_admin_api_key or not hmac.compare_digest(
        x_admin_api_key,
        expected_api_key,
    ):
        raise HTTPException(
            status_code=401,
            detail="A valid admin API key is required.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
