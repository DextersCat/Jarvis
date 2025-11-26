from __future__ import annotations

from enum import Enum
from typing import Dict, Set

from .agent_domains import AgentDomain


class DecisionOutcome(Enum):
    ACCEPT = "accept"
    CLARIFY = "clarify"


AGENT_CAPABILITIES: Dict[AgentDomain, Set[str]] = {
    AgentDomain.EMAIL: {"send_email", "send_copy", "read_last_email_from", "summarize_inbox"},
    AgentDomain.CALENDAR: {"create_event", "show_agenda_today", "show_events_on_date"},
    AgentDomain.TASKS: {"create_reminder", "list_tasks", "complete_task"},
    AgentDomain.SEARCH: {"search_web", "search_emails", "search_docs"},
    AgentDomain.DOCS: {"open_doc", "summarize_doc"},
    AgentDomain.MEMORY: {"store_note", "recall_note", "list_notes"},
    AgentDomain.ROBOTICS: {"get_status", "run_safe_routine"},
    AgentDomain.VISION: {"show_camera", "check_presence"},
    AgentDomain.SYSTEM: {"list_files", "read_file", "show_system_status"},
    AgentDomain.PERSONA: {"set_tone", "set_voice_mode", "enable_bork_mode"},
}


def is_action_supported(agent: AgentDomain, action: str) -> bool:
    """Return True if this agent supports the given action name."""
    return action in AGENT_CAPABILITIES.get(agent, set())

