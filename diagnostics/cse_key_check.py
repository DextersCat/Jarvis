#!/usr/bin/env python3
"""
Custom Search key check.
Uses env GOOGLE_SEARCH_API_KEY / GOOGLE_SEARCH_CX and calls:
https://customsearch.googleapis.com/customsearch/v1?q=jarvis test&num=1
Prints cx, key hash (sha256), key last4, HTTP status, and JSON body.
"""

import hashlib
import json
import os
import urllib.parse
import urllib.request

from dotenv import load_dotenv

ROOT_ENV = "/root/JARVIS/.env"
load_dotenv(ROOT_ENV)
load_dotenv()


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def main() -> int:
    key = os.getenv("GOOGLE_SEARCH_API_KEY", "")
    cx = os.getenv("GOOGLE_SEARCH_CX", "")
    print(f"cx: {cx}")
    if key:
        print(f"key_sha256: {hash_key(key)}")
        print(f"key_last4: {key[-4:]}")
    else:
        print("key missing")

    params = {
        "key": key,
        "cx": cx,
        "q": "jarvis test",
        "num": 1,
    }
    url = "https://customsearch.googleapis.com/customsearch/v1?" + urllib.parse.urlencode(params)
    print(f"Request URL (key hidden): https://customsearch.googleapis.com/customsearch/v1?cx={cx}&q=jarvis+test&num=1&key=***")

    req = urllib.request.Request(url, method="GET")
    status = None
    body = b""
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            body = resp.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read()
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error: {exc!r}")
        return 1

    try:
        data = json.loads(body.decode("utf-8")) if body else {}
    except Exception:
        data = body.decode("utf-8", errors="ignore") if body else ""

    print(f"HTTP status: {status}")
    print("Response:", json.dumps(data, indent=2) if isinstance(data, dict) else data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
