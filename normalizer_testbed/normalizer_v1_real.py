from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Dict, Tuple, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

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
from .mapping_config_v1 import map_natural_to_canonical


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

    def __init__(self, model_name: str = "llama3:latest") -> None:
        self.model_name = model_name
        self._log_initialized = False

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
            agent_scores_raw = payload.get("agent_scores") or {}
            intent_payload = payload.get("intent") or {}
            llm_confidence_raw = intent_payload.get("confidence")
            try:
                llm_confidence = float(llm_confidence_raw)
            except Exception:
                llm_confidence = 0.0

            natural_domain = intent_payload.get("domain")
            natural_action = intent_payload.get("action")
            canonical_domain, canonical_action = map_natural_to_canonical(natural_domain, natural_action)
            if canonical_domain and canonical_action:
                intent_payload["domain"] = canonical_domain
                intent_payload["action"] = canonical_action
            else:
                self._log_unmapped_intent(
                    raw_text=raw_text,
                    natural_domain=natural_domain,
                    natural_action=natural_action,
                    llm_confidence=llm_confidence,
                )
                return IntentObject(
                    domain="clarify",
                    action="ask_clarification",
                    search_term=None,
                    parameters={
                        "cause": "unknown_domain_or_action",
                        "natural_domain": natural_domain,
                        "natural_action": natural_action,
                    },
                    confidence=0.0,
                    fuzzy_allowed=False,
                    question="I'm not sure which part of Jarvis should handle this yet. Could you rephrase or be more specific?",
                    raw=raw_text,
                )

            agent_scores_adjusted = self._sharpen_scores_for_domain(
                agent_scores_raw.copy(),
                intent_payload.get("domain"),
                llm_confidence,
            )
            agent_scores = self._build_agent_scores(agent_scores_adjusted)
            proposed = ProposedIntent(
                domain=str(intent_payload.get("domain") or "").strip(),
                action=str(intent_payload.get("action") or "").strip(),
            )
            decision_outcome: Optional[Outcome] = None
            selection = None
            try:
                decision_outcome, selection = decide_intent_outcome(agent_scores, proposed)
            finally:
                self._log_cycle1_raw(
                    raw_input=raw_text,
                    agent_scores_raw=agent_scores_raw,
                    intent_raw=intent_payload,
                    llm_confidence=llm_confidence,
                    llm_fuzzy_allowed=bool(intent_payload.get("fuzzy_allowed", False)),
                    decision_outcome=decision_outcome,
                    decision_reason=(selection.kind.value if selection else None),
                )

            outcome = decision_outcome
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

    def _sharpen_scores_for_domain(
        self,
        scores: Dict[str, Any],
        proposed_domain: Optional[str],
        confidence: float,
    ) -> Dict[str, Any]:
        """
        Down-weight competing agents when the LLM shows high confidence in a specific domain.
        """
        domain_to_agent_key = {
            "email": "email_agent",
            "calendar": "calendar_agent",
            "tasks": "tasks_agent",
            "search": "search_agent",
            "docs": "docs_agent",
            "memory": "memory_agent",
            "robotics": "robotics_agent",
            "vision": "vision_agent",
            "system": "system_agent",
            "persona": "persona_agent",
        }

        if not proposed_domain or proposed_domain not in domain_to_agent_key:
            return scores
        if confidence < 0.8:
            return scores

        chosen_agent = domain_to_agent_key[proposed_domain]
        if chosen_agent not in scores:
            return scores

        try:
            chosen_score = float(scores[chosen_agent])
        except Exception:
            return scores

        if chosen_score < 0.8:
            return scores

        threshold = chosen_score - 0.2
        for agent_key, score in scores.items():
            if agent_key == chosen_agent:
                continue
            try:
                score_val = float(score)
            except Exception:
                continue
            if score_val >= threshold:
                scores[agent_key] = min(score_val, 0.5)

        return scores

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
        log_path = Path("/mnt/c/Users/spenc/JARVIS-Workspace/tests/normalizer_v1_real_ollama_debug_run2.log")
        timestamp = datetime.now(timezone.utc).isoformat()
        try:
            if not self._log_initialized:
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with log_path.open("w", encoding="utf-8") as logf:
                    logf.write(f"NormalizerV1 Run2 log start @ {timestamp}, model={self.model_name}\n")
                self._log_initialized = True
            proc = subprocess.run(
                ["ollama", "run", self.model_name],
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            output = proc.stdout.decode("utf-8", errors="ignore")
            stderr = proc.stderr.decode("utf-8", errors="ignore")
            # Extract JSON even if prefixed with prose
            text = output.strip()
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end < start:
                raise ValueError("No JSON object found in LLM output")
            json_str = text[start : end + 1]
            with log_path.open("a", encoding="utf-8") as logf:
                logf.write(f"\n--- OLLAMA CALL @ {timestamp} model={self.model_name} ---\n")
                logf.write("PROMPT:\n")
                logf.write(prompt + "\n")
                logf.write("STDOUT:\n")
                logf.write(output + "\n")
                logf.write("EXTRACTED_JSON:\n")
                logf.write(json_str + "\n")
                if stderr:
                    logf.write("STDERR:\n")
                    logf.write(stderr + "\n")
            return json.loads(json_str)
        except Exception as exc:
            try:
                with log_path.open("a", encoding="utf-8") as logf:
                    logf.write(f"\n--- OLLAMA ERROR @ {timestamp} model={self.model_name} ---\n")
                    logf.write("PROMPT:\n")
                    logf.write(prompt + "\n")
                    logf.write(f"ERROR: {exc}\n")
            except Exception:
                pass
            return None

    def _log_cycle1_raw(
        self,
        raw_input: str,
        agent_scores_raw: Dict[str, Any],
        intent_raw: Dict[str, Any],
        llm_confidence: Any,
        llm_fuzzy_allowed: bool,
        decision_outcome: Optional[Outcome],
        decision_reason: Optional[str],
    ) -> None:
        """Append raw LLM output + decision outcome for Cycle 1 diagnostics."""
        diagnostics_path = Path("/mnt/c/Users/spenc/JARVIS-Workspace/tests/normalizer_cycle1_raw_llm_output.jsonl")
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "raw_input": raw_input,
            "agent_scores_raw": agent_scores_raw,
            "intent_raw": intent_raw,
            "llm_confidence": None,
            "llm_fuzzy_allowed": bool(llm_fuzzy_allowed),
            "decision_engine_outcome": decision_outcome.name if decision_outcome else None,
            "decision_engine_reason": decision_reason,
        }

        try:
            record["llm_confidence"] = float(llm_confidence)
        except Exception:
            record["llm_confidence"] = None

        try:
            diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
            with diagnostics_path.open("a", encoding="utf-8") as diag:
                json.dump(record, diag, ensure_ascii=False)
                diag.write("\n")
        except Exception:
            # Swallow logging errors to avoid impacting main flow
            pass

    def _log_unmapped_intent(
        self,
        raw_text: str,
        natural_domain: Optional[str],
        natural_action: Optional[str],
        llm_confidence: float,
    ) -> None:
        """Log unmapped natural intents for future mapping refinement."""
        log_path = Path("/mnt/c/Users/spenc/JARVIS-Workspace/tests/normalizer_unmapped_intents_v1.jsonl")
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "raw": raw_text,
            "natural_domain": natural_domain,
            "natural_action": natural_action,
            "llm_confidence": llm_confidence,
        }
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False)
                f.write("\n")
        except Exception:
            pass


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
