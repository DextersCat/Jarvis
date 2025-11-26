from __future__ import annotations

from enum import Enum
from typing import List, Dict


class AgentDomain(Enum):
    EMAIL = "email_agent"
    CALENDAR = "calendar_agent"
    TASKS = "tasks_agent"
    SEARCH = "search_agent"
    DOCS = "docs_agent"
    MEMORY = "memory_agent"
    ROBOTICS = "robotics_agent"
    VISION = "vision_agent"
    SYSTEM = "system_agent"
    PERSONA = "persona_agent"


def all_agent_domains() -> List[AgentDomain]:
    """Return all agent domains in a fixed order."""
    return [
        AgentDomain.EMAIL,
        AgentDomain.CALENDAR,
        AgentDomain.TASKS,
        AgentDomain.SEARCH,
        AgentDomain.DOCS,
        AgentDomain.MEMORY,
        AgentDomain.ROBOTICS,
        AgentDomain.VISION,
        AgentDomain.SYSTEM,
        AgentDomain.PERSONA,
    ]


def agent_identifier_map() -> Dict[AgentDomain, str]:
    """Convenience mapping from domain to identifier string."""
    return {domain: domain.value for domain in all_agent_domains()}

