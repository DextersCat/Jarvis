#!/usr/bin/env python3
"""Minimal Gmail diagnostic: list count of unread messages (max 5)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services import email_service


def main() -> int:
    print("[GMAIL] Using module:", email_service.__file__)
    print("[GMAIL] Scopes:", email_service.SCOPES)
    try:
        service = email_service._load_gmail_service()
        resp = (
            service.users()
            .messages()
            .list(userId="me", q="is:unread", maxResults=5)
            .execute()
        )
        count = len(resp.get("messages", []))
        print(f"[GMAIL] PASS: fetched {count} unread message ids")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[GMAIL] FAIL: {exc!r}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
