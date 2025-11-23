#!/usr/bin/env python3
"""Minimal Calendar diagnostic: list next 5 events."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services import calendar_service


def main() -> int:
    print("[CALENDAR] Using module:", calendar_service.__file__)
    print("[CALENDAR] Scopes:", calendar_service.SCOPES)
    try:
        service = calendar_service._load_calendar_service()
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                maxResults=5,
                singleEvents=True,
                orderBy="startTime",
                timeMin=calendar_service._time_window_for_day(0)[0],
            )
            .execute()
        )
        items = events_result.get("items", [])
        print(f"[CALENDAR] PASS: fetched {len(items)} events")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[CALENDAR] FAIL: {exc!r}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
