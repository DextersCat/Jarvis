"""
Identity resolver for email senders.
Loads a persisted map from ~/.jarvis_tokens/identity_map.json if present,
falls back to built-in defaults, and supports fuzzy matching on sender fields.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

IDENTITY_STORE = Path.home() / ".jarvis_tokens" / "identity_map.json"

# Seed defaults; extend as needed.
DEFAULT_IDENTITY_MAP: Dict[str, List[str]] = {
    "SPENCER DIXON": [
        "spencerdixon.dixon@gmail.com",
        "spencerdixon@gmail.com",
        "spencer@btconnect.com",
        "spencer@dixon.family",
    ],
    "JAMIE DIXON": [
        "jamie@vayro.co.uk",
        "jamie.dixon@vayro.co.uk",
    ],
    "AMAZON": [
        "amazon.co.uk",
        "amazon.com",
        "amazonservices.com",
        "payments.amazon.co.uk",
        "no-reply@payments.amazon.co.uk",
        "no-reply@amazon.co.uk",
    ],
}


def _load_identity_map() -> Dict[str, List[str]]:
    if IDENTITY_STORE.exists():
        try:
            data = json.loads(IDENTITY_STORE.read_text())
            if isinstance(data, dict):
                return {k: v for k, v in data.items() if isinstance(v, list)}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load identity map: %s", exc)
    return DEFAULT_IDENTITY_MAP.copy()


def _save_identity_map(data: Dict[str, List[str]]) -> None:
    try:
        IDENTITY_STORE.parent.mkdir(parents=True, exist_ok=True)
        IDENTITY_STORE.write_text(json.dumps(data, indent=2, sort_keys=True))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to save identity map: %s", exc)


IDENTITY_MAP: Dict[str, List[str]] = _load_identity_map()


def normalize_token(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def resolve_input_identity(name: str) -> Tuple[Optional[str], List[str]]:
    """Resolve user-provided sender name to canonical identity and tokens."""
    tokens = [normalize_token(t) for t in name.split() if normalize_token(t)]
    if not tokens:
        return None, []
    canonical = None
    for ident, aliases in IDENTITY_MAP.items():
        ident_tokens = [normalize_token(t) for t in ident.split() if normalize_token(t)]
        if all(tok in ident_tokens for tok in tokens):
            canonical = ident
            break
    return canonical, tokens


def match_sender_fields(fields: Dict[str, str]) -> Optional[str]:
    """Match sender using known identity map against multiple header fields."""
    haystack_parts = []
    for key in ("from", "reply_to", "return_path", "x_sender", "envelope_from"):
        val = fields.get(key) or ""
        haystack_parts.append(val)
    haystack = " ".join(haystack_parts).lower()
    for ident, aliases in IDENTITY_MAP.items():
        for alias in aliases:
            alias_norm = alias.lower()
            if alias_norm in haystack:
                return ident
            alias_root = normalize_token(alias_norm)
            if alias_root and alias_root in normalize_token(haystack):
                return ident
    return None


def add_identity(canonical: str, aliases: List[str]) -> None:
    """Add or extend an identity and persist."""
    if not canonical:
        return
    existing = IDENTITY_MAP.get(canonical) or []
    merged = list({*existing, *aliases})
    IDENTITY_MAP[canonical] = merged
    _save_identity_map(IDENTITY_MAP)
