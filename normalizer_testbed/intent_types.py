from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum, auto
from typing import Any, Dict, Optional


class ConfidenceBucket(Enum):
    HIGH = auto()
    MEDIUM = auto()
    LOW = auto()


def bucket_confidence(conf: float) -> ConfidenceBucket:
    try:
        value = float(conf)
    except Exception:
        return ConfidenceBucket.LOW
    if value >= 0.80:
        return ConfidenceBucket.HIGH
    if value >= 0.50:
        return ConfidenceBucket.MEDIUM
    return ConfidenceBucket.LOW


@dataclass
class IntentObject:
    domain: str
    action: str
    search_term: Optional[str]
    parameters: Dict[str, Any]
    confidence: float
    fuzzy_allowed: bool
    question: Optional[str]
    raw: str


def intent_as_dict(intent: IntentObject) -> Dict[str, Any]:
    """Return a plain dict for debug/printing."""
    return asdict(intent)

