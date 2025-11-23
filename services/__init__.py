"""Service layer modules for Jarvis Brain."""

from .search_service import search_web, summarise_search_results
from .email_service import (
    fetch_unread_summary,
    write_email_summary,
    build_markdown,
    build_email_markdown,
    search_messages_in_window,
    mark_messages_read,
    search_messages_by_criteria,
    fetch_full_message,
    send_reply,
)
from .calendar_service import (
    get_today_agenda,
    get_tomorrow_agenda,
    get_next_important_event,
    write_calendar_briefing,
    build_daily_markdown,
)

__all__ = [
    "search_web",
    "summarise_search_results",
    "fetch_unread_summary",
    "write_email_summary",
    "build_markdown",
    "build_email_markdown",
    "search_messages_in_window",
    "mark_messages_read",
    "search_messages_by_criteria",
    "fetch_full_message",
    "send_reply",
    "get_today_agenda",
    "get_tomorrow_agenda",
    "get_next_important_event",
    "write_calendar_briefing",
    "build_daily_markdown",
]
