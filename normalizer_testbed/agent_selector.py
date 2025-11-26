from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

from .agent_domains import AgentDomain, all_agent_domains


@dataclass
class AgentScores:
    scores: Dict[AgentDomain, float]


class SelectionKind(Enum):
    CLEAR_MATCH = "clear_match"
    AMBIGUOUS = "ambiguous"
    NO_GOOD_MATCH = "no_good_match"


@dataclass
class AgentSelectionResult:
    kind: SelectionKind
    top_agent: Optional[AgentDomain]
    second_agent: Optional[AgentDomain]
    top_score: float
    second_score: float
    reason: str


def _sorted_scores(agent_scores: AgentScores) -> Tuple[Optional[AgentDomain], float, Optional[AgentDomain], float]:
    """Return top and second agent with scores; missing entries default to 0.0."""
    # Ensure all domains are present
    full_scores = {domain: 0.0 for domain in all_agent_domains()}
    full_scores.update(agent_scores.scores or {})

    sorted_items = sorted(full_scores.items(), key=lambda kv: kv[1], reverse=True)
    top_agent, top_score = sorted_items[0]
    if len(sorted_items) > 1:
        second_agent, second_score = sorted_items[1]
    else:
        second_agent, second_score = None, 0.0
    return top_agent, float(top_score), second_agent, float(second_score)


def select_agent(agent_scores: AgentScores) -> AgentSelectionResult:
    """
    Apply selection rules to agent scores.

    Rule A: CLEAR_MATCH if top_score >= 0.80 and gap >= 0.20
    Rule B: AMBIGUOUS if top_score >= 0.50 and gap < 0.20
    Rule C: NO_GOOD_MATCH if top_score < 0.50
    """
    top_agent, top_score, second_agent, second_score = _sorted_scores(agent_scores)
    gap = top_score - second_score

    if top_score >= 0.80 and gap >= 0.20:
        return AgentSelectionResult(
            kind=SelectionKind.CLEAR_MATCH,
            top_agent=top_agent,
            second_agent=second_agent,
            top_score=top_score,
            second_score=second_score,
            reason=f"Clear winner: {top_agent.name} score={top_score:.2f}, gap={gap:.2f}",
        )

    if top_score >= 0.50 and gap < 0.20:
        return AgentSelectionResult(
            kind=SelectionKind.AMBIGUOUS,
            top_agent=top_agent,
            second_agent=second_agent,
            top_score=top_score,
            second_score=second_score,
            reason=f"Ambiguous: {top_agent.name} vs {second_agent.name if second_agent else 'none'} gap={gap:.2f}",
        )

    # top_score < 0.50
    return AgentSelectionResult(
        kind=SelectionKind.NO_GOOD_MATCH,
        top_agent=top_agent,
        second_agent=second_agent,
        top_score=top_score,
        second_score=second_score,
        reason=f"No good match: top={top_agent.name if top_agent else 'none'} score={top_score:.2f}",
    )

