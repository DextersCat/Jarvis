import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from typing import Any

from typing import Any, Dict
from googleapiclient.errors import HttpError
from services import google_helper

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
DEFAULT_TZ = "Europe/London"


def _load_calendar_service() -> object:
    logger.info("Calendar requested scopes: %s", SCOPES)
    return google_helper.build_service("calendar")


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


def get_events_between(start_dt: datetime, end_dt: datetime, max_results: int = 20) -> List[Dict]:
    service = _load_calendar_service()
    try:
        events = _fetch_events(service, start_dt.isoformat(), end_dt.isoformat(), max_results=max_results)
        logger.info("Calendar events fetched between %s and %s: %d", start_dt, end_dt, len(events))
        return events
    except HttpError as exc:
        logger.error("Calendar range fetch failed: %s", exc)
        raise


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


def create_event(event_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an event in the primary calendar.
    event_spec keys: title, start (datetime), end (datetime or None), all_day (bool), description, location, timezone.
    """
    service = google_helper.build_service("calendar")
    summary = event_spec.get("title") or "Untitled"
    description = event_spec.get("description") or "Created by Jarvis."
    location = event_spec.get("location")
    all_day = bool(event_spec.get("all_day"))
    tz = event_spec.get("timezone") or DEFAULT_TZ
    start_dt = event_spec.get("start")
    end_dt = event_spec.get("end")

    if not start_dt:
        raise ValueError("Event start time is required.")

    def _ensure_tz(dt):
        if hasattr(dt, "tzinfo") and dt.tzinfo:
            return dt
        return dt.replace(tzinfo=timezone.utc)

    body: Dict[str, Any] = {
        "summary": summary,
        "description": description,
    }

    if all_day:
        start_date = start_dt.date()
        end_date = end_dt.date() if end_dt else (start_date + timedelta(days=1))
        body["start"] = {"date": start_date.isoformat()}
        body["end"] = {"date": end_date.isoformat()}
    else:
        start_dt = _ensure_tz(start_dt)
        if not end_dt:
            end_dt = start_dt + timedelta(minutes=60)
        else:
            end_dt = _ensure_tz(end_dt)
        body["start"] = {"dateTime": start_dt.isoformat(), "timeZone": tz}
        body["end"] = {"dateTime": end_dt.isoformat(), "timeZone": tz}

    if location:
        body["location"] = location

    try:
        logger.info("[CalendarCreate] Inserting event summary=%s start=%s end=%s all_day=%s",
                    summary, body.get("start"), body.get("end"), all_day)
        event = service.events().insert(calendarId="primary", body=body).execute()
        return {
            "success": True,
            "id": event.get("id"),
            "summary": event.get("summary"),
            "start": event.get("start"),
            "end": event.get("end"),
            "htmlLink": event.get("htmlLink"),
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("[CalendarCreate] Failed to create event: %s", exc)
        return {"success": False, "error": str(exc)}


def update_event(event_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    service = google_helper.build_service("calendar")
    try:
        event = service.events().patch(calendarId="primary", eventId=event_id, body=patch).execute()
        logger.info("[CalendarUpdate] Updated event id=%s summary=%s", event_id, event.get("summary"))
        return {
            "success": True,
            "action": "update_event",
            "details": {
                "id": event.get("id"),
                "summary": event.get("summary"),
                "start": event.get("start"),
                "end": event.get("end"),
                "htmlLink": event.get("htmlLink"),
            },
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("[CalendarUpdate] Failed to update event %s: %s", event_id, exc)
        return {"success": False, "action": "update_event", "details": {"id": event_id, "error": str(exc)}}


def delete_event(event_id: str) -> Dict[str, Any]:
    service = google_helper.build_service("calendar")
    try:
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        logger.info("[CalendarDelete] Deleted event id=%s", event_id)
        return {"success": True, "action": "delete_event", "details": {"id": event_id}}
    except Exception as exc:  # noqa: BLE001
        logger.error("[CalendarDelete] Failed to delete event %s: %s", event_id, exc)
        return {"success": False, "action": "delete_event", "details": {"id": event_id, "error": str(exc)}}
