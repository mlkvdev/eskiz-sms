"""Probe the live Eskiz API for the correct paths/methods of two endpoints
that currently 404 in the SDK: prices and sms-check.

Logs in once, then tries every plausible (method, path, body-style) variant
and reports the status code for each. Any 2xx is a candidate; anything that
returns JSON (rather than nginx plaintext) is also a useful clue.

Run:
    uv run python scripts/probe_endpoints.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env.integration"

try:
    from dotenv import load_dotenv

    load_dotenv(ENV_PATH)
except ImportError:
    print("python-dotenv missing; run with `uv run`", file=sys.stderr)
    sys.exit(1)


BASE = os.environ.get("ESKIZ_BASE_URL", "https://notify.eskiz.uz/api")
EMAIL = os.environ["ESKIZ_EMAIL"]
PASSWORD = os.environ["ESKIZ_PASSWORD"]


def login(client: httpx.Client) -> str:
    r = client.post(
        f"{BASE}/auth/login",
        data={"email": EMAIL, "password": PASSWORD},
    )
    r.raise_for_status()
    return r.json()["data"]["token"]


def short(body: str | bytes | None, n: int = 120) -> str:
    if body is None:
        return ""
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    body = body.replace("\n", " ").strip()
    return body[:n] + ("…" if len(body) > n else "")


def probe(
    client: httpx.Client,
    token: str,
    method: str,
    path: str,
    *,
    json: dict | None = None,
    data: dict | None = None,
    params: dict | None = None,
) -> tuple[int, str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    r = client.request(
        method,
        f"{BASE}{path}",
        headers=headers,
        json=json,
        data=data,
        params=params,
    )
    ctype = r.headers.get("content-type", "").split(";")[0]
    body = short(r.text)
    return r.status_code, ctype, body


PRICES_VARIANTS: list[tuple[str, str, dict]] = [
    ("GET", "/user/prices", {}),
    ("GET", "/user/get-prices", {}),
    ("GET", "/user/get-price", {}),
    ("GET", "/user/price", {}),
    ("POST", "/user/prices", {}),
    ("GET", "/report/prices", {}),
    ("GET", "/report/price", {}),
]

CHECK_VARIANTS: list[tuple[str, str, dict]] = [
    ("GET", "/message/sms/check", {"json": {"message": "test"}}),
    ("POST", "/message/sms/check", {"json": {"message": "test"}}),
    ("POST", "/message/sms/check", {"data": {"message": "test"}}),
    ("GET", "/message/sms/check", {"params": {"message": "test"}}),
    ("POST", "/message/sms/check-symbols", {"data": {"message": "test"}}),
    ("POST", "/message/sms/symbols", {"data": {"message": "test"}}),
    ("GET", "/message/check", {"params": {"message": "test"}}),
    ("POST", "/sms/check", {"data": {"message": "test"}}),
]


def main() -> None:
    with httpx.Client(timeout=15.0) as client:
        token = login(client)
        print(f"logged in OK, token len={len(token)}\n")

        print("=== PRICES variants ===")
        for method, path, kwargs in PRICES_VARIANTS:
            status, ctype, body = probe(client, token, method, path, **kwargs)
            mark = "OK " if 200 <= status < 300 else "   "
            print(f"  {mark}{method:5} {path:40} -> {status} {ctype:20} {body}")

        print("\n=== SMS CHECK variants ===")
        for method, path, kwargs in CHECK_VARIANTS:
            label_extra = ",".join(k for k in kwargs)
            status, ctype, body = probe(client, token, method, path, **kwargs)
            mark = "OK " if 200 <= status < 300 else "   "
            print(
                f"  {mark}{method:5} {path:40} ({label_extra:6}) -> "
                f"{status} {ctype:20} {body}"
            )


if __name__ == "__main__":
    main()
