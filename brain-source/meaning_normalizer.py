"""
AstraMeaningNormalizer - converts messy user text into a structured intent.

This sits between raw STT/GUI text and the router. It is intentionally thin and
swap-friendly: update the prompt or LLM call here to evolve Astra without
touching the router or agents.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


class AstraMeaningNormalizer:
    """
    Normalize raw text into a structured intent dict using the local LLM.

    Public API:
        normalize(raw_text: str) -> Dict[str, Any]

    Output schema (minimal):
        {
            "domain": str,            # one of: email, web_search, calendar, general_task, clarify
            "action": str,            # e.g., search, create, update, summarize
            "search_term": str,       # optional; core query term
            "confidence": float,
            "fuzzy_allowed": bool,
            "parameters": dict,       # optional parameters per domain
            "question": str           # only for clarify domain
        }
    """

    SAMPLE_LOG_LIMIT = 5

    def __init__(self, llm_client, model: str = "llama3"):
        self.llm_client = llm_client
        self.model = model
        self._sample_logs = 0

    def normalize(self, raw_text: str) -> Dict[str, Any]:
        safe_text = (raw_text or "").strip()
        if not safe_text:
            return {
                "domain": "clarify",
                "question": "Sir, what would you like me to do?",
                "confidence": 0.0,
                "fuzzy_allowed": False,
                "parameters": {},
            }

        prompt = self._build_prompt(safe_text)
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": safe_text},
                ],
                max_tokens=180,
                temperature=0.2,
            )
            text = response.choices[0].message.content if response and response.choices else ""
        except Exception as exc:  # noqa: BLE001
            logger.warning("[Normalizer] LLM call failed: %s", exc)
            return {
                "domain": "clarify",
                "question": "Sir, what exactly would you like me to do?",
                "confidence": 0.0,
                "fuzzy_allowed": False,
                "parameters": {},
            }

        intent = self._parse_intent_text(text)
        if self._sample_logs < self.SAMPLE_LOG_LIMIT:
            logger.info("[Normalizer] Sample intent: raw='%s' -> %s", safe_text[:80], intent)
            self._sample_logs += 1
        return intent

    @staticmethod
    def _build_prompt(raw_text: str) -> str:
        return (
            "You normalize noisy voice transcription into a minimal intent JSON.\n"
            "Respond ONLY with a JSON object, no prose.\n"
            "Constraints:\n"
            "- Domains allowed: email, web_search, calendar, general_task, clarify\n"
            "- Actions allowed: search, summarize, create, update, delete, query, none\n"
            "- NEVER fabricate email content; you only extract intent/queries.\n"
            "- If confidence < 0.4, set domain='clarify' and include a clarifying question.\n"
            "- Preserve/repair key subject words (e.g., 'pyvision' -> 'Pi Vision', 'nvidea' -> 'Nvidia').\n"
            "- For email search phrases (search/find/look in my email/gmail/inbox/messages), set domain=email, action=search, and put the core query in search_term.\n"
            "- For web searches (look up / search the web / google), set domain=web_search, action=search, search_term=<query>.\n"
            "- For calendar add/update/delete, set domain=calendar and action=create/update/delete; include title/time/date hints in parameters.\n"
            "- For generic tasks ('remind me', 'todo'), set domain=general_task and action=create.\n"
            "- fuzzy_allowed: true if spelling may need correction or fuzzy match, else false.\n"
            "Output JSON fields:\n"
            "{\n"
            '  "domain": <domain>,\n'
            '  "action": <action>,\n'
            '  "search_term": <string or "" if none>,\n'
            '  "confidence": <0-1>,\n'
            '  "fuzzy_allowed": <true|false>,\n'
            '  "parameters": { ... },\n'
            '  "question": <clarifying question if domain is clarify>\n'
            "}\n"
            "Input will be messy STT. Normalize and return only JSON."
        )

    @staticmethod
    def _parse_intent_text(text: str) -> Dict[str, Any]:
        import json

        default_intent = {
            "domain": "clarify",
            "question": "Sir, what exactly would you like me to do?",
            "confidence": 0.0,
            "fuzzy_allowed": False,
            "parameters": {},
            "search_term": "",
            "action": "none",
        }

        if not text:
            return default_intent
        try:
            obj = json.loads(text)
            domain = obj.get("domain") or "clarify"
            action = obj.get("action") or "none"
            confidence = float(obj.get("confidence", 0) or 0)
            search_term = obj.get("search_term") or ""
            fuzzy_allowed = bool(obj.get("fuzzy_allowed", False))
            params = obj.get("parameters") if isinstance(obj.get("parameters"), dict) else {}
            question = obj.get("question") or default_intent["question"]

            # Clamp domain to allowed set
            if domain not in {"email", "web_search", "calendar", "general_task", "clarify"}:
                domain = "clarify"

            if confidence < 0.0 or confidence > 1.0:
                confidence = max(0.0, min(1.0, confidence))

            intent = {
                "domain": domain,
                "action": action,
                "search_term": search_term,
                "confidence": confidence,
                "fuzzy_allowed": fuzzy_allowed,
                "parameters": params,
                "question": question,
            }

            if confidence < 0.4:
                intent["domain"] = "clarify"
                intent["action"] = "none"
            return intent
        except Exception as exc:  # noqa: BLE001
            logger.warning("[Normalizer] Failed to parse intent JSON: %s", exc)
            return default_intent

