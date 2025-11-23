#!/usr/bin/env python3
"""
Multi-service Google diagnostics for Jarvis.
Reports PASS / NOT CONFIGURED / INSUFFICIENT SCOPE / FAIL per API.
"""

import json
from pathlib import Path
from typing import Dict

import sys
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services import google_helper as gh

# Load optional project-level .env for API keys
load_dotenv(ROOT / ".env")
load_dotenv()

def gmail_check() -> Dict:
    from services import email_service

    return gh.check_oauth_service("gmail", lambda svc: len(
        svc.users().messages().list(userId="me", q="is:unread", maxResults=1).execute().get("messages", [])
    ))


def calendar_check() -> Dict:
    from services import calendar_service

    return gh.check_oauth_service(
        "calendar",
        lambda svc: len(
            svc.events()
            .list(
                calendarId="primary",
                maxResults=1,
                singleEvents=True,
                orderBy="startTime",
                timeMin=calendar_service._time_window_for_day(0)[0],
            )
            .execute()
            .get("items", [])
        ),
    )


def tasks_check() -> Dict:
    return gh.check_oauth_service(
        "tasks",
        lambda svc: len(svc.tasks().list(tasklist="@default", maxResults=1).execute().get("items", [])),
    )


def docs_check() -> Dict:
    return gh.check_oauth_service(
        "docs",
        lambda svc: bool(svc.documents().get(documentId="about:blank").execute()),
    )


def sheets_check() -> Dict:
    return gh.check_oauth_service(
        "sheets",
        lambda svc: len(
            svc.spreadsheets()
            .values()
            .get(spreadsheetId="about:blank", range="A1:A1")
            .execute()
            .get("values", [])
        ),
    )


def slides_check() -> Dict:
    return gh.check_oauth_service(
        "slides",
        lambda svc: bool(svc.presentations().get(presentationId="about:blank").execute()),
    )


def drive_check() -> Dict:
    return gh.check_oauth_service(
        "drive",
        lambda svc: len(svc.files().list(pageSize=1, fields="files(id)").execute().get("files", [])),
    )


def cse_check() -> Dict:
    def _call():
        import urllib.parse
        import urllib.request
        import os

        key = os.getenv("GOOGLE_SEARCH_API_KEY")
        cx = os.getenv("GOOGLE_SEARCH_CX")
        if not key or not cx:
            raise RuntimeError("Missing GOOGLE_SEARCH_API_KEY/GOOGLE_SEARCH_CX")
        url = f"https://www.googleapis.com/customsearch/v1?q=jarvis&key={key}&cx={cx}&num=1"
        with urllib.request.urlopen(url, timeout=5) as resp:
            return f"status={resp.status}"

    return gh.check_api_key_service("custom_search", ("GOOGLE_SEARCH_API_KEY", "GOOGLE_SEARCH_CX"), _call)


def gemini_check() -> Dict:
    return gh.check_gemini()


def main():
    checks = {
        "gmail": gmail_check,
        "calendar": calendar_check,
        "tasks": tasks_check,
        "docs": docs_check,
        "sheets": sheets_check,
        "slides": slides_check,
        "drive": drive_check,
        "custom_search": cse_check,
        "gemini": gemini_check,
    }
    results = {}
    for name, fn in checks.items():
        try:
            results[name] = fn()
        except Exception as exc:  # noqa: BLE001
            results[name] = {"status": "FAIL", "detail": repr(exc)}
    print(json.dumps(results, indent=2))
    summary = ", ".join(f"{k}:{v.get('status')}" for k, v in results.items())
    print(f"Summary: {summary}")

    log_dir = Path("/root/JARVIS/runtime/logs/google")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"google_services_check_{Path(__file__).stem}.log"
    log_path.write_text(json.dumps(results, indent=2))
    print(f"Results logged to {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
