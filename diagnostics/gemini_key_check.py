#!/usr/bin/env python3
"""
Minimal Gemini key check using AI Studio cURL pattern.
GET https://generativelanguage.googleapis.com/v1beta/models?key=API_KEY
No OAuth; key via query param.
"""

import json
import os
import urllib.error
import urllib.request
from dotenv import load_dotenv

ROOT_ENV = "/root/JARVIS/.env"
load_dotenv(ROOT_ENV)
load_dotenv()

def redact(key: str) -> str:
    if not key:
        return ""
    return key[:-4] + "****"

def main():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GENAI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY/GOOGLE_GENAI_API_KEY set.")
        return 1

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    print(f"URL: https://generativelanguage.googleapis.com/v1beta/models?key={redact(api_key)}")

    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
            status = resp.status
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
