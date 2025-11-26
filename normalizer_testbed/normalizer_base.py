from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from .intent_types import IntentObject


class BaseNormalizer(ABC):
    """
    Base interface for all normalizers.

    Implementations must never return partial objects. All fields of the
    IntentObject must be populated, even on error/clarification.
    """

    @abstractmethod
    def normalize(self, raw_text: str) -> IntentObject:
        """Convert raw text into a fully populated IntentObject."""
        raise NotImplementedError


class EchoNormalizer(BaseNormalizer):
    """
    TEMPORARY STUB: Echoes back a clarify intent.

    Used to prove the test harness; expected to fail all golden cases until a
    real normalizer is plugged in.
    """

    def normalize(self, raw_text: str) -> IntentObject:
        return IntentObject(
            domain="clarify",
            action="ask_clarification",
            search_term=None,
            parameters={},
            confidence=0.0,
            fuzzy_allowed=False,
            question="Testbed stub only – NormalizerV1 not implemented yet.",
            raw=raw_text,
        )

