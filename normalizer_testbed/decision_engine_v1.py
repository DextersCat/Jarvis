from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .agent_domains import AgentDomain
from .agent_selector import AgentScores, AgentSelectionResult, SelectionKind, select_agent
from .capability_registry import DecisionOutcome, is_action_supported


@dataclass
class ProposedIntent:
    domain: str
    action: str


def _domain_string_from_agent(agent: AgentDomain) -> str:
    mapping = {
        AgentDomain.EMAIL: "email",
        AgentDomain.CALENDAR: "calendar",
        AgentDomain.TASKS: "tasks",
        AgentDomain.SEARCH: "search",
        AgentDomain.DOCS: "docs",
        AgentDomain.MEMORY: "memory",
        AgentDomain.ROBOTICS: "robotics",
        AgentDomain.VISION: "vision",
        AgentDomain.SYSTEM: "system",
        AgentDomain.PERSONA: "persona",
    }
    return mapping.get(agent, "")


def decide_intent_outcome(
    scores: AgentScores,
    proposed: ProposedIntent,
) -> Tuple[DecisionOutcome, AgentSelectionResult]:
    """
    Decide ACCEPT vs CLARIFY based on agent scores and capabilities.
    Returns (DecisionOutcome, AgentSelectionResult).
    """
    selection = select_agent(scores)

    if selection.kind in {SelectionKind.NO_GOOD_MATCH, SelectionKind.AMBIGUOUS}:
        return DecisionOutcome.CLARIFY, selection

    # CLEAR_MATCH path
    top_agent = selection.top_agent
    if not top_agent:
        return DecisionOutcome.CLARIFY, selection

    domain_str = _domain_string_from_agent(top_agent)
    if proposed.domain != domain_str:
        return DecisionOutcome.CLARIFY, selection

    if not is_action_supported(top_agent, proposed.action):
        return DecisionOutcome.CLARIFY, selection

    return DecisionOutcome.ACCEPT, selection

