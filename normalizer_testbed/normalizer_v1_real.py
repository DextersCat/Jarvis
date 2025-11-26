from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Dict, Tuple

from .normalizer_base import BaseNormalizer
from .intent_types import IntentObject
from .agent_domains import AgentDomain
from .agent_selector import AgentScores
from .decision_engine_v1 import (
    ProposedIntent,
    decide_intent_outcome,
    DecisionOutcome,
)
from .capability_registry import DecisionOutcome as Outcome


_AGENT_KEY_MAP: Dict[str, AgentDomain] = {
    "email_agent": AgentDomain.EMAIL,
    "calendar_agent": AgentDomain.CALENDAR,
    "tasks_agent": AgentDomain.TASKS,
    "search_agent": AgentDomain.SEARCH,
    "docs_agent": AgentDomain.DOCS,
    "memory_agent": AgentDomain.MEMORY,
    "robotics_agent": AgentDomain.ROBOTICS,
    "vision_agent": AgentDomain.VISION,
    "system_agent": AgentDomain.SYSTEM,
    "persona_agent": AgentDomain.PERSONA,
}


_PROMPT_TEMPLATE = """You are an intent normalizer for JARVIS. Given user text, output EXACTLY one JSON object:
{
  "agent_scores": {
    "email_agent": 0.0-1.0,
    "calendar_agent": 0.0-1.0,
    "tasks_agent": 0.0-1.0,
    "search_agent": 0.0-1.0,
    "docs_agent": 0.0-1.0,
    "memory_agent": 0.0-1.0,
    "robotics_agent": 0.0-1.0,
    "vision_agent": 0.0-1.0,
    "system_agent": 0.0-1.0,
    "persona_agent": 0.0-1.0
  },
  "intent": {
    "domain": "<email|calendar|tasks|search|docs|memory|robotics|vision|system|persona|clarify>",
    "action": "<string>",
    "search_term": "<string or null>",
    "parameters": { ... JSON object ... },
    "confidence": 0.0-1.0,
    "fuzzy_allowed": <true|false>,
    "question": "<string or null if clarify>"
  }
}
Rules:
- Assign a score to ALL agents (0.0 allowed).
- Domain must align with the chosen agent notion (email/search/etc.) or 'clarify'.
- Unknown nouns stay as-is (do NOT correct or expand).
- Respond with JSON ONLY, no prose.
User text: """


class NormalizerV1(BaseNormalizer):
    """
    Real Normalizer V1 that calls an LLM via Ollama to interpret raw_text
    into an intent proposal and agent scores, then applies the existing
    decision engine and builds a final IntentObject.
    """

    def __init__(self, model_name: str = "llama3.1:8b-instruct") -> None:
        self.model_name = model_name

    def normalize(self, raw_text: str) -> IntentObject:
        if not raw_text or not raw_text.strip():
            return IntentObject(
                domain="clarify",
                action="ask_clarification",
                search_term=None,
                parameters={},
                confidence=0.0,
                fuzzy_allowed=False,
                question="I didn't catch that. What would you like me to do?",
                raw=raw_text,
            )

        prompt_text = " ".join(raw_text.split())
        payload = self._call_ollama(prompt_text)
        if payload is None:
            return self._clarify_fallback(raw_text, cause="llm_error")

        try:
            agent_scores = self._build_agent_scores(payload.get("agent_scores") or {})
            intent_payload = payload.get("intent") or {}
            proposed = ProposedIntent(
                domain=str(intent_payload.get("domain") or "").strip(),
                action=str(intent_payload.get("action") or "").strip(),
            )
            outcome, selection = decide_intent_outcome(agent_scores, proposed)
            if outcome == Outcome.CLARIFY:
                # Clarify reasons based on selection kind
                cause = "no_good_match"
                if selection.kind.name.lower().startswith("ambiguous"):
                    cause = "ambiguous"
                elif not proposed.domain:
                    cause = "missing_domain"
                return self._clarify_fallback(raw_text, cause=cause)

            # ACCEPT path
            domain = proposed.domain or "clarify"
            action = proposed.action or "ask_clarification"
            search_term = intent_payload.get("search_term")
            parameters = intent_payload.get("parameters")
            if not isinstance(parameters, dict):
                parameters = {"value": parameters} if parameters is not None else {}
            fuzzy_allowed = bool(intent_payload.get("fuzzy_allowed", False))
            # Enforce false for risky domains
            if domain in {"email", "tasks", "system", "robotics"}:
                fuzzy_allowed = False
            confidence = intent_payload.get("confidence")
            try:
                confidence = float(confidence)
            except Exception:
                confidence = 0.0
            confidence = max(0.0, min(1.0, confidence))
            question = intent_payload.get("question") if domain == "clarify" else None

            return IntentObject(
                domain=domain,
                action=action,
                search_term=search_term,
                parameters=parameters,
                confidence=confidence,
                fuzzy_allowed=fuzzy_allowed,
                question=question,
                raw=raw_text,
            )
        except Exception:
            return self._clarify_fallback(raw_text, cause="llm_parse_error")

    def _clarify_fallback(self, raw_text: str, cause: str) -> IntentObject:
        return IntentObject(
            domain="clarify",
            action="ask_clarification",
            search_term=None,
            parameters={"cause": cause},
            confidence=0.0,
            fuzzy_allowed=False,
            question="I'm having trouble understanding your request right now. Could you rephrase it?",
            raw=raw_text,
        )

    def _build_agent_scores(self, scores_dict: Dict[str, float]) -> AgentScores:
        scores: Dict[AgentDomain, float] = {}
        for key, agent in _AGENT_KEY_MAP.items():
            raw_score = scores_dict.get(key, 0.0)
            try:
                scores[agent] = float(raw_score)
            except Exception:
                scores[agent] = 0.0
        return AgentScores(scores=scores)

    def _call_ollama(self, prompt_text: str) -> Dict:
        prompt = _PROMPT_TEMPLATE + prompt_text
        try:
            proc = subprocess.run(
                ["ollama", "run", self.model_name],
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            output = proc.stdout.decode("utf-8")
            return json.loads(output)
        except Exception:
            return None


if __name__ == "__main__":
    norm = NormalizerV1()
    samples = [
        "remind me tomorrow at 10 to call jamie",
        "search my emails for pyvision",
        "switch to bork mode",
    ]
    for s in samples:
        result = norm.normalize(s)
        print(result)

