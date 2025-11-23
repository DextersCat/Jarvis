import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

TOKEN_DIR = Path.home() / ".jarvis_tokens"
CALENDAR_TOKEN_FILE = TOKEN_DIR / "calendar_token.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
DEFAULT_TZ = "Europe/London"


def _load_calendar_service() -> object:
    if not CALENDAR_TOKEN_FILE.exists():
        raise FileNotFoundError(f"Calendar token missing: {CALENDAR_TOKEN_FILE}")
    creds = Credentials.from_authorized_user_file(str(CALENDAR_TOKEN_FILE), SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError("Calendar credentials invalid; please re-authenticate.")
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _time_window_for_day(day_offset: int = 0) -> Tuple[str, str]:
    tz = timezone.utc
    now = datetime.now(tz) + timedelta(days=day_offset)
    start = datetime(now.year, now.month, now.day, tzinfo=tz)
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def _fetch_events(service, time_min: str, time_max: str, max_results: int = 20) -> List[Dict]:
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=max_results,
        )
        .execute()
    )
    events = events_result.get("items", [])
    parsed = []
    for ev in events:
        start = ev.get("start", {})
        end = ev.get("end", {})
        start_str = start.get("dateTime") or start.get("date")
        end_str = end.get("dateTime") or end.get("date")
        all_day = "date" in start
        parsed.append(
            {
                "title": ev.get("summary", "(no title)"),
                "start": start_str,
                "end": end_str,
                "location": ev.get("location"),
                "is_all_day": all_day,
            }
        )
    return parsed


def get_today_agenda() -> List[Dict]:
    service = _load_calendar_service()
    time_min, time_max = _time_window_for_day(0)
    try:
        events = _fetch_events(service, time_min, time_max)
        logger.info("Calendar today events fetched: %d", len(events))
        return events
    except HttpError as exc:
        logger.error("Calendar today fetch failed: %s", exc)
        raise


def get_tomorrow_agenda() -> List[Dict]:
    service = _load_calendar_service()
    time_min, time_max = _time_window_for_day(1)
    try:
        events = _fetch_events(service, time_min, time_max)
        logger.info("Calendar tomorrow events fetched: %d", len(events))
        return events
    except HttpError as exc:
        logger.error("Calendar tomorrow fetch failed: %s", exc)
        raise


def get_next_important_event() -> Optional[Dict]:
    service = _load_calendar_service()
    now = datetime.now(timezone.utc)
    try:
        events = _fetch_events(
            service, now.isoformat(), (now + timedelta(days=30)).isoformat(), max_results=10
        )
    except HttpError as exc:
        logger.error("Calendar next event fetch failed: %s", exc)
        raise
    logger.info("Calendar next event fetched: %d", len(events))
    return events[0] if events else None


def build_daily_markdown(day_label: str, events: List[Dict]) -> str:
    now = datetime.now(timezone.utc)
    lines = [
        f"# Calendar Briefing: {day_label}",
        "",
        f"**Timestamp:** {now.isoformat()}  ",
        "**Category:** calendar  ",
        "**Source:** calendar_service  ",
        f"**Context:** {day_label} agenda",
        "",
        "## Events",
    ]
    if not events:
        lines.append("No events.")
    else:
        for idx, ev in enumerate(events, start=1):
            title = ev.get("title")
            start = ev.get("start")
            end = ev.get("end")
            loc = ev.get("location") or ""
            all_day = ev.get("is_all_day")
            timing = "All day" if all_day else f"{start} → {end}"
            lines.append(f"{idx}. **{title}**")
            lines.append(f"   {timing}")
            if loc:
                lines.append(f"   Location: {loc}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_calendar_briefing(file_service, day_label: str, events: List[Dict]) -> Optional[str]:
    if not file_service or not file_service.is_enabled:
        return None
    now = datetime.now()
    name = f"{now.strftime('%H%M')}_daily-briefing"
    content = build_daily_markdown(day_label, events)
    result = file_service.create_file(
        name=name,
        ext="md",
        category="calendar",
        content=content,
        allow_overwrite=False,
    )
    if result.get("success"):
        return result.get("full_path")
    logger.warning("Failed to write calendar briefing: %s", result.get("message"))
    return None
