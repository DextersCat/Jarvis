#!/usr/bin/env python3
"""
JARVIS Brain Module - Ubuntu WSL2 Version
PC Brain Migration - Phase C1

This is the core processing brain without audio I/O.
Designed to work with AI-Pi voice terminal via WebSocket.

Based on: Fresh Professional Astra AI with JARVIS Personality Framework
"""

import asyncio
import inspect
import logging
import os
import platform
import psutil
import re
import socket
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from openai import OpenAI

os.environ.setdefault("ANONYMIZED_TELEMETRY", "FALSE")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
logging.getLogger("chromadb").setLevel(logging.ERROR)
logging.getLogger("chromadb.telemetry").setLevel(logging.ERROR)

# Ensure project root is importable for shared services
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import identity_resolver
from meaning_normalizer import AstraMeaningNormalizer

# JARVIS personality modules
from personality_engine import PersonalityEngine
from context_manager import ContextManager
from proactive_engine import ProactiveSuggestionEngine
from jarvis_memory_system import JARVISMemory
from file_service import JarvisFileService
from services.search_service import search_web, summarise_search_results
from services import google_helper
from agents.email_agent import EmailAgent
from agents.web_search_agent import WebSearchAgent
from agents.memory_agent import MemoryAgent
from agents.calendar_agent import CalendarAgent
from agents.docs_agent import DocsAgent
from agents.local_docs_agent import LocalDocsSearchAgent
from agents.system_agent import SystemAgent
from services.email_service import (
    fetch_unread_summary,
    write_email_summary,
    build_email_markdown,
    search_messages_in_window,
    mark_messages_read,
    mark_messages_read_action,
    mark_messages_unread,
    archive_messages,
    delete_messages,
    apply_label,
    send_email,
    mark_inbox_unread,
    search_messages_by_criteria,
    fetch_full_message,
    send_reply,
    write_daily_email_summary_section,
    list_inbox_messages,
)
from services.calendar_service import (
    get_today_agenda,
    get_tomorrow_agenda,
    get_next_important_event,
    write_calendar_briefing,
    create_event as calendar_create_event,
    update_event as calendar_update_event,
    delete_event as calendar_delete_event,
)
from services.library_index import (
    add_item as add_library_item,
    get_latest as get_latest_library_item,
    upsert_item as upsert_library_item,
)
from services.email_classifier import classify_email
from llm_profiles import select_profile

# Load environment variables
ENV_PATH = Path.home() / "JARVIS" / "config" / ".env"
load_dotenv(ENV_PATH)
# Optional project-level overrides
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv()

logger = logging.getLogger(__name__)
LONG_QUERY_THRESHOLD = 350
SPOKEN_LENGTH_WATERMARK = 1200
MAX_CHAT_TOKENS = 200
MAX_EMAIL_SEARCH_HISTORY = 24
MAX_WEB_SEARCH_HISTORY = 24
HUD_FOLLOWUP_DOMAINS = {"email", "web_search", "calendar", "docs", "memory", "system"}

class JARVISBrain:
    """
    JARVIS Brain - Core Intelligence System
    Runs on Ubuntu WSL2 with GPU acceleration
    """
    
    def __init__(self):
        print("=" * 60)
        print("­ƒºá JARVIS BRAIN - PC INTELLIGENCE CORE")
        print("=" * 60)
        print("­ƒÜÇ Initializing Ubuntu WSL2 Brain Module...")
        print("")
        
        # Core configuration
        # HYBRID: Ollama Llama3 for GPT, OpenAI for TTS (fable voice)
        profile = select_profile()
        self.ai_model = profile.get("model", "llama3")
        self.llm_profile = profile.get("name")
        self.llm_base_url = profile.get("base_url")
        self.llm_api_key = profile.get("api_key")
        self.voice_model = "tts-1"
        self.voice_type = "fable"
        
        # Location data
        self.latitude = float(os.getenv('USER_LATITUDE', 51.172096))
        self.longitude = float(os.getenv('USER_LONGITUDE', 0.498793))
        self.location_name = "Kent, UK"
        
        # Stats tracking
        self.stats = {
            'conversations': 0,
            'calculations_performed': 0,
            'weather_requests': 0,
            'system_commands': 0,
            'start_time': datetime.now()
        }
        self.conversation_state = {
            "awaiting_followup": False,
            "last_question_id": None,
        }
        self.active_followup_question_id = None
        self.pending_choices = {}
        self._pending_email_search_results: dict[str, list[dict[str, Any]]] = {}
        self._pending_email_reply_drafts: dict[str, dict[str, Any]] = {}
        self._last_email_focus: dict[str, Any] | None = None
        self._pending_web_search_results: dict[str, list[dict[str, Any]]] = {}
        self.current_web_result: dict[str, Any] | None = None
        self._last_web_focus: dict[str, Any] | None = None
        self._pending_web_reply_refresh: dict[str, Any] | None = None
        self.pending_mark_read = None
        self.current_email = None
        self.current_email_identity = None
        self.pending_reply = None
        self.email_edit_context: dict[str, Any] | None = None
        self.email_agent = EmailAgent()
        self.meaning_normalizer = None

        # File service (stub, non-destructive)
        self.file_service = self._init_file_service()
        
        # System info
        self.system_info = self._get_system_info()
        
        # Initialize components
        self.init_brain_system()
        self._init_normalizer()
    
    def _get_system_info(self):
        """Get detailed system information"""
        return {
            'platform': f"{platform.system()} {platform.release()} ({platform.machine()})",
            'hostname': socket.gethostname(),
            'cores': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq().max if psutil.cpu_freq() else 0,
            'memory_total': round(psutil.virtual_memory().total / (1024**3), 2),
            'gpu_available': self._check_gpu()
        }
    
    def _check_gpu(self):
        """Check if GPU is available"""
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return result.stdout.strip()
            return False
        except:
            return False

    def _init_file_service(self):
        """Initialise the stubbed Jarvis file service with env-based base path."""
        vault_path = os.getenv("JARVIS_VAULT_PATH")
        service = JarvisFileService(base_path=vault_path) if vault_path else JarvisFileService(base_path=None)

        if service.base_path:
            print(f"FileService initialised -> {service.base_path}")
        else:
            if vault_path:
                print("FileService disabled: invalid JARVIS_VAULT_PATH (no file ops will run).")
            else:
                print("FileService disabled: JARVIS_VAULT_PATH not set (file ops offline).")

        return service

    def _init_normalizer(self):
        """Initialise AstraMeaningNormalizer."""
        try:
            self.meaning_normalizer = AstraMeaningNormalizer(self.openai_client, model=self.ai_model)
            logger.info("[Normalizer] AstraMeaningNormalizer initialised (model=%s)", self.ai_model)
        except Exception as exc:  # noqa: BLE001
            self.meaning_normalizer = None
            logger.warning("[Normalizer] Failed to initialise: %s", exc)

    def _preview_text(self, text: str, limit: int) -> str:
        """Return a safe preview of text for logging."""
        if text is None:
            return ""
        return text[:limit] + ("..." if len(text) > limit else "")

    def _detect_simple_intent(self, text: str) -> str:
        """Lightweight intent hinting for handshake logging."""
        if not text:
            return "empty"
        lowered = text.lower()
        if any(word in lowered for word in ["email", "inbox", "gmail"]):
            return "email"
        if any(word in lowered for word in ["calendar", "meeting", "schedule"]):
            return "calendar"
        if "search" in lowered or "google" in lowered:
            return "web_search"
        if "task" in lowered or "todo" in lowered:
            return "tasks"
        if "time" in lowered or "date" in lowered:
            return "time_query"
        return "general"

    def _run_conversation_handshake(self, raw_text: str) -> dict:
        """
        Run the 3-phase handshake to validate and log incoming text.
        Returns dict with final_text and intent for downstream use.
        """
        received_text = (raw_text or "").strip()
        logger.info("[HANDSHAKE] Phase 1 – Received text: '%s'", self._preview_text(received_text, 80))

        intent = self._detect_simple_intent(received_text)
        logger.info("[HANDSHAKE] Phase 2 – Heuristic intent guess (logging only): %s", intent)

        final_text = received_text
        logger.info(
            "[HANDSHAKE] Phase 3 – Final text to LLM (len=%d, preview='%s')",
            len(final_text),
            self._preview_text(final_text, 80),
        )

        return {
            "final_text": final_text,
            "intent": intent,
        }

    def _generate_question_id(self) -> str:
        """Generate a short question identifier for follow-ups."""
        return uuid.uuid4().hex[:8]

    def _detect_followup_prompt(self, response_text: str) -> bool:
        """Detect if the assistant is asking a follow-up question."""
        if not response_text:
            return False
        lowered = response_text.lower()
        if "would you like more detail" in lowered:
            return True
        if "would you like a deeper dive" in lowered:
            return True
        if lowered.strip().endswith("?") and "sir" in lowered:
            return True
        return False

    def _is_followup_affirmation(self, text: str) -> bool:
        """Detect simple affirmative follow-up cues."""
        if not text:
            return False
        lowered = text.lower().strip()
        affirmations = [
            "yes",
            "yeah",
            "sure",
            "okay",
            "ok",
            "please",
            "tell me more",
            "more detail",
            "more details",
            "a deeper dive",
            "deeper dive",
            "go deeper",
            "continue",
        ]
        return any(lowered == a or lowered.endswith(a) for a in affirmations)

    def _build_followup_choices(self, question_id: str, topic: str | None = None, handler: str | None = None, metadata: dict | None = None) -> dict:
        """Construct a standardized follow-up choices payload."""
        topic_label = topic or "General follow-up"
        choices = {
            "A": f"Deeper dive on {topic_label}",
            "B": f"Alternate angle on {topic_label}",
            "C": f"Action on this topic (open resource / create note)",
        }
        payload = {
            "question_id": question_id,
            "topic": topic_label,
            "choices": choices,
        }
        if handler:
            payload["handler"] = handler
        if metadata:
            payload["metadata"] = metadata
        self.pending_choices[question_id] = payload
        return payload

    def _build_followup_prompt(self, choice_key: str, payload: dict) -> str:
        """Build a concrete follow-up prompt for the LLM."""
        topic = payload.get("topic") or "this topic"
        choice_text = payload.get("choices", {}).get(choice_key, "")
        if choice_key == "A":
            return f"Please give me a deeper dive into {topic}, expanding on the previous answer."
        if choice_key == "B":
            return f"Please provide an alternate angle or additional context on {topic}, building on the previous answer."
        # Default fallback for unexpected key
        return f"Please continue with more detail on {topic}."

    def _perform_followup_action(self, payload: dict) -> str:
        """Placeholder for action choice C - stub with minimal behavior."""
        topic = payload.get("topic") or "this topic"
        try:
            # If a file service is configured, drop a note stub.
            if self.file_service and getattr(self.file_service, "is_enabled", False):
                content = f"Follow-up action for topic: {topic}\nGenerated: {datetime.now().isoformat()}\n\n(No action implemented; placeholder note.)"
                result = self.file_service.create_file(
                    name="followup_action",
                    ext="md",
                    category="actions",
                    content=content,
                )
                if result.get("success"):
                    return f"Logged an action note for {topic}: {result.get('full_path')}"
            return f"Action placeholder recorded for {topic} (no further action implemented)."
        except Exception as exc:  # noqa: BLE001
            logger.warning("[FOLLOWUP] Action stub failed: %s", exc)
            return f"Action placeholder for {topic} (failed to write note: {exc})"

    async def _process_followup_prompt(self, question_id: str, choices: list[str]):
        """Handle structured follow-up choices (A/B/C)."""
        payload = self.pending_choices.get(question_id)
        if not payload:
            logger.warning("[FOLLOWUP] No pending choices for question_id=%s", question_id)
            return "I couldn't find the prior topic to continue, Sir."

        logger.info("[FOLLOWUP] choices=%s topic='%s'", choices, payload.get("topic"))
        responses = []
        # Clear follow-up waiting state for this branch
        self.conversation_state["awaiting_followup"] = False
        self.conversation_state["last_question_id"] = None

        for choice in choices:
            if choice in ("A", "B"):
                prompt = self._build_followup_prompt(choice, payload)
                logger.info("[FOLLOWUP] Built prompt for choice %s: '%s'", choice, prompt)
                # Run through normal pipeline
                resp = await self.process_text_input(prompt)
                responses.append(resp if isinstance(resp, str) else resp.get("spoken_text", ""))
            elif choice == "C":
                action_msg = self._perform_followup_action(payload)
                responses.append(action_msg)
            else:
                logger.warning("[FOLLOWUP] Unknown choice '%s' for question_id=%s", choice, question_id)

        # Clear pending choices after processing
        self.pending_choices.pop(question_id, None)
        # Join responses sensibly
        combined = "\n\n".join(r for r in responses if r)
        return combined or "Follow-up processed."

    async def process_followup_choice(self, question_id: str, choices: list[str]):
        """Public entry for structured follow-up choices (A/B/C)."""
        if not question_id:
            logger.warning("[FOLLOWUP] Missing question_id in followup_choice")
            return "I need to know which question you're following up on, Sir."
        if not choices:
            logger.warning("[FOLLOWUP] Empty choices list for question_id=%s", question_id)
            return "I didn't receive which option you wanted, Sir."
        if self.active_followup_question_id and question_id != self.active_followup_question_id:
            logger.warning(
                "[FOLLOWUP] Received choice for stale question_id=%s (active=%s)",
                question_id,
                self.active_followup_question_id,
            )
            return "That follow-up is no longer active, Sir."

        preserve_reply_options = False
        result = None
        first_choice = choices[0] if choices else None
        email_actions = ("open_email", "summarise_email", "search_docs_from_email")
        web_actions = ("open_web_result", "summarise_web_result", "search_docs_from_web_result")
        if first_choice in email_actions:
            preserve_reply_options = True
            result = await self._handle_email_hud_followup(question_id, choices)
        elif first_choice in web_actions:
            preserve_reply_options = True
            result = await self._handle_web_hud_followup(question_id, choices)
        elif question_id in self._pending_email_search_results:
            preserve_reply_options = True
            result = await self._handle_email_search_selection(question_id, choices)
        elif question_id in self._pending_web_search_results:
            preserve_reply_options = True
            result = await self._handle_web_search_selection(question_id, choices)
        elif question_id in self._pending_email_reply_drafts:
            result = await self._handle_email_reply_choice(question_id, choices)
        else:
            payload = self.pending_choices.get(question_id)
            if payload and payload.get("handler") == "email_bulk_mark_read":
                result = await self._handle_email_bulk_followup(payload, choices)
            elif payload and payload.get("handler") == "calendar_delete_event":
                result = await self._handle_calendar_delete_followup(payload, choices)
            elif payload and payload.get("handler") == "email_delete":
                result = await self._handle_email_delete_followup(payload, choices)
            elif payload and payload.get("handler") == "web_search_followup":
                result = await self._handle_web_search_followup(payload, choices)
            elif payload and payload.get("handler") == "email_reply_followup":
                result = await self._handle_email_reply_followup(payload, choices)
            else:
                result = await self._process_followup_prompt(question_id, choices)

        refresh_data = self._pending_web_reply_refresh
        self._pending_web_reply_refresh = None
        if not preserve_reply_options:
            self.active_followup_question_id = None
            await self._clear_reply_options(question_id)
            if refresh_data:
                await self._send_web_reply_options(**refresh_data)
        return result

    async def _emit_hud_event(self, payload: dict) -> bool:
        """Safely emit HUD event if sink is available. Returns success flag."""
        sink = getattr(self, "hud_event_sink", None)
        if not sink:
            return False
        try:
            result = sink(payload)
            if inspect.isawaitable(result):
                await result
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("[HUD_ERROR] Failed to send HUD event: %s", exc)
            return False

    async def _send_to_hud(self, payload: dict[str, Any]) -> bool:
        """Wrapper around `_emit_hud_event` for clarity."""
        return await self._emit_hud_event(payload)

    async def _emit_followup_choices(self, payload: dict[str, Any], domain: str) -> bool:
        """Emit follow-up choices only for whitelisted domains."""
        if domain not in HUD_FOLLOWUP_DOMAINS:
            logger.info(
                "[HUD] Skipping reply options for domain=%s (HUD isolation active)",
                domain,
            )
            return False
        return await self._emit_hud_event(payload)

    async def _clear_reply_options(self, question_id: str | None = None):
        """Clear reply options on HUD (defensive)."""
        try:
            if hasattr(self, "hud_event_sink") and callable(self.hud_event_sink):
                await self._emit_hud_event({
                    "type": "followup_choices",
                    "question_id": None,
                    "choices": {},
                    "topic": None,
                })
                logger.info("[FOLLOWUP] Clearing reply options for qid=%s", question_id or "none")
                logger.info("[HUD] Cleared reply options")
        except Exception as exc:  # noqa: BLE001
            logger.warning("[HUD_ERROR] Failed to clear reply options: %s", exc)

    def _activate_followup(self, question_id: str, topic: str | None):
        """Record the current follow-up and keep HUD logs in sync."""
        self.active_followup_question_id = question_id
        self.conversation_state["awaiting_followup"] = True
        self.conversation_state["last_question_id"] = question_id
        logger.info(
            "[FOLLOWUP] Activated followup question_id=%s topic=%s",
            question_id,
            topic or "unknown",
        )

    def _ensure_default_reply_options(
        self,
        query_id: str | None,
        reply_options: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        """
        Guarantee that HUD reply options are non-empty and include a default end-query option.
        """
        options = list(reply_options or [])
        if options:
            return options
        default_option = {
            "id": "end_query",
            "label": "End this query",
            "kind": "core",
            "action": "cancel",
        }
        if query_id:
            default_option["query_id"] = query_id
        options.append(default_option)
        return options

    def _prepare_hud_payload(
        self,
        payload: dict[str, Any],
        query_id: str | None,
        reply_options: list[dict[str, Any]] | None = None,
        reset_hud: bool = False,
    ) -> dict[str, Any]:
        """
        Clone the HUD payload and ensure it carries reply options + optional reset flag.
        """
        enriched = dict(payload)
        if "metadata" in enriched and isinstance(enriched["metadata"], dict):
            enriched["metadata"] = dict(enriched["metadata"])

        existing_options = enriched.pop("reply_options", None) or []
        merged_options = []
        if isinstance(existing_options, list):
            merged_options.extend(existing_options)
        else:
            merged_options.append(existing_options)
        if reply_options:
            merged_options.extend(reply_options)
        enriched["reply_options"] = self._ensure_default_reply_options(query_id, merged_options)
        if reset_hud:
            enriched["reset_hud"] = True
        return enriched

    async def _send_hud_panel(
        self,
        payload: dict[str, Any],
        *,
        query_id: str | None = None,
        reply_options: list[dict[str, Any]] | None = None,
        reset_hud: bool = False,
    ) -> bool:
        """
        Emit a HUD panel update payload with consistent reply options and reset flag.
        """
        enriched = self._prepare_hud_payload(payload, query_id, reply_options=reply_options, reset_hud=reset_hud)
        return await self._emit_hud_event(enriched)

    async def _send_panel_reset(self, query_id: str | None = None):
        """Reset HUD focus/context panels and reply options before handling a new query."""
        if not hasattr(self, "hud_event_sink") or not callable(self.hud_event_sink):
            return

        metadata_base = {"reset": True}
        if query_id:
            metadata_base["query_id"] = query_id

        focus_payload = {
            "type": "hud_panel_update",
            "panel": "focus",
            "mode": "list",
            "source": "brain",
            "title": "",
            "items": [],
            "metadata": dict(metadata_base),
        }
        context_payload = {
            "type": "hud_panel_update",
            "panel": "context",
            "mode": "list",
            "source": "brain",
            "title": "",
            "items": [],
            "metadata": dict(metadata_base),
        }

        try:
            await self._send_hud_panel(focus_payload, query_id=query_id, reset_hud=True)
            await self._send_hud_panel(context_payload, query_id=query_id, reset_hud=True)
            logger.info("[HUD] Panel reset for query_id=%s", query_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[HUD_ERROR] Panel reset failed: %s", exc)

    async def _reset_hud_for_new_query(self, query_id: str):
        """Clear HUD state and caches when a new query arrives."""
        if not query_id:
            return
        self.active_followup_question_id = None
        self.conversation_state["awaiting_followup"] = False
        self.conversation_state["last_question_id"] = None
        self.current_email = None
        self.current_web_result = None
        self._last_email_focus = None
        self._last_web_focus = None
        self._pending_web_reply_refresh = None
        await self._clear_reply_options(query_id)
        await self._send_hud_result_list("brain", query_id, [])
        await self._send_panel_reset(query_id)

    async def _handle_hud_clear(self):
        """Reset HUD and cancel any active follow-ups without running agents."""
        self.pending_choices.clear()
        self._pending_email_search_results.clear()
        self._pending_web_search_results.clear()
        self.pending_mark_read = None
        self.current_email = None
        self.current_web_result = None
        self._last_email_focus = None
        self._last_web_focus = None
        self.active_followup_question_id = None
        self.conversation_state["awaiting_followup"] = False
        self.conversation_state["last_question_id"] = None
        self._pending_web_reply_refresh = None
        query_id = self._generate_question_id()
        await self._reset_hud_for_new_query(query_id)

    async def _send_hud_result_list(
        self,
        source: str,
        query_id: str,
        items: list[dict[str, Any]],
    ):
        """Send a normalized result list panel update for HUD column 2."""
        if not hasattr(self, "hud_event_sink") or not callable(self.hud_event_sink):
            return
        payload = {
            "type": "hud_panel_update",
            "panel": "context",
            "mode": "list",
            "source": source,
            "title": f"{source.replace('_', ' ').title()} results",
            "items": items,
            "metadata": {"query_id": query_id},
        }
        try:
            await self._send_hud_panel(payload, query_id=query_id)
            logger.info("[HUD] panel=context mode=list source=%s items=%d", source, len(items))
        except Exception as exc:  # noqa: BLE001
            logger.warning("[HUD_ERROR] Failed to send %s result list: %s", source, exc)

    async def _send_focus_panel(self, query_id: str | None, query: str, focus_text: str | None):
        if not focus_text:
            return
        title = f"Web search: {self._preview_text(query, 60)}" if query else "Web search"
        payload = {
            "type": "hud_panel_update",
            "panel": "focus",
            "mode": "markdown",
            "source": "web_search",
            "title": title,
            "markdown": focus_text,
            "metadata": {
                "query": query,
                "query_id": query_id,
            },
        }
        sent = await self._send_hud_panel(payload, query_id=query_id)
        if sent:
            logger.info("[WebHUD] Focus sent for query_id=%s", query_id)

    async def _send_context_panel(self, query_id: str | None, query: str, context_points: list[str]):
        if not context_points:
            return
        title = f"Context for {self._preview_text(query, 60)}" if query else "Web context"
        items = [{"title": point} for point in context_points[:6]]
        payload = {
            "type": "hud_panel_update",
            "panel": "context",
            "mode": "list",
            "source": "web_search",
            "title": title,
            "items": items,
            "metadata": {
                "query": query,
                "query_id": query_id,
            },
        }
        sent = await self._send_hud_panel(payload, query_id=query_id)
        if sent:
            logger.info("[WebHUD] Context sent for query_id=%s", query_id)

    async def _send_web_reply_options(
        self,
        query_id: str | None,
        query: str,
        topic: str,
        style: str,
    ):
        if not query_id:
            query_id = self._generate_question_id()
        choices = {
            "A": "Deeper dive",
            "B": "Different angle",
            "C": "Short recap",
        }
        payload = {
            "type": "followup_choices",
            "question_id": query_id,
            "topic": topic,
            "choices": choices,
            "handler": "web_search_followup",
            "query": query,
            "style": style,
            "metadata": {"query": query, "style": style},
        }
        self.pending_choices[query_id] = {
            "question_id": query_id,
            "handler": "web_search_followup",
            "topic": topic,
            "query": query,
            "style": style,
        }
        self._activate_followup(query_id, topic)
        sent = await self._emit_followup_choices(payload, "email")
        if sent:
            logger.info("[WebHUD] Followup choices A/B/C sent for query_id=%s", query_id)

    def _schedule_web_reply_options(self, query_id: str | None, query: str, topic: str, style: str):
        self._pending_web_reply_refresh = {
            "query_id": query_id,
            "query": query,
            "topic": topic,
            "style": style,
        }

    async def _send_email_focus_panel(self, query_id: str | None, email_meta: dict[str, Any]):
        if not email_meta:
            return
        focus_data = self.email_agent.build_focus_payload(email_meta)
        payload = {
            "type": "hud_panel_update",
            "panel": "focus",
            "mode": "cards",
            "source": "email",
            "title": focus_data.get("subject"),
            "items": [
                {
                    "title": focus_data.get("sender"),
                    "subtitle": focus_data.get("snippet"),
                    "metadata": {
                        "timestamp": focus_data.get("timestamp"),
                        "thread_id": focus_data.get("thread_id"),
                        "message_id": focus_data.get("message_id"),
                    },
                }
            ],
            "metadata": {"query_id": query_id, "thread_id": focus_data.get("thread_id")},
        }
        if await self._send_hud_panel(payload, query_id=query_id):
            logger.info("[EmailHUD] Focus sent for query_id=%s", query_id)

    async def _send_email_context_summary(self, query_id: str | None, summary: str):
        if not summary:
            return
        context_data = self.email_agent.build_context_summary(summary)
        payload = {
            "type": "hud_panel_update",
            "panel": "context",
            "mode": "list",
            "source": "email",
            "title": "Email summary",
            "items": [{"title": "Summary", "subtitle": context_data.get("summary")}],
            "metadata": {"query_id": query_id},
        }
        if await self._send_hud_panel(payload, query_id=query_id):
            logger.info("[EmailHUD] Context sent for query_id=%s", query_id)

    async def _send_email_context_draft(self, query_id: str | None, draft: str):
        if not draft:
            return
        context_data = self.email_agent.build_context_draft(draft)
        payload = {
            "type": "hud_panel_update",
            "panel": "context",
            "mode": "markdown",
            "source": "email",
            "title": "Draft reply",
            "markdown": draft,
            "metadata": {"query_id": query_id},
        }
        if await self._send_hud_panel(payload, query_id=query_id):
            logger.info("[EmailHUD] Context draft sent for query_id=%s", query_id)

    async def _send_email_context_status(self, query_id: str | None, status: str):
        if not status:
            return
        payload = {
            "type": "hud_panel_update",
            "panel": "context",
            "mode": "list",
            "source": "email",
            "title": "Email status",
            "items": [{"title": status}],
            "metadata": {"query_id": query_id},
        }
        await self._send_hud_panel(payload, query_id=query_id)
        logger.info("[EmailHUD] Context status sent for query_id=%s", query_id)

    def _normalize_email_search_result(self, message: dict[str, Any]) -> dict[str, Any]:
        """Normalise HUD-facing email search items."""
        return {
            "id": message.get("id"),
            "threadId": message.get("threadId") or message.get("thread_id"),
            "subject": message.get("subject"),
            "from": message.get("from"),
            "date": message.get("date"),
            "snippet": message.get("snippet"),
        }

    def _build_email_focus_record(self, meta: dict[str, Any], body: str | None = None) -> dict[str, Any]:
        """Create a sanitized record used for focus/context updates."""
        normalized_body = body or meta.get("body") or ""
        snippet = meta.get("snippet") or (normalized_body or "")[:240]
        return {
            "id": meta.get("id"),
            "threadId": meta.get("threadId") or meta.get("thread_id"),
            "from": meta.get("from"),
            "subject": meta.get("subject") or "Email",
            "date": meta.get("date"),
            "body": normalized_body,
            "snippet": snippet,
        }

    async def _activate_email_focus_from_record(self, query_id: str | None, record: dict[str, Any]):
        """Update brain focus state and HUD panels for the provided email."""
        if not record:
            return
        self.current_email = record
        self.current_email_identity = None
        self._last_email_focus = dict(record)
        await self._send_email_focus_panel(query_id, record)
        summary_text = record.get("body") or record.get("snippet") or "Summary unavailable."
        await self._send_email_context_summary(query_id, summary_text)

    async def _handle_email_hud_followup(self, question_id: str, choices: list[str]) -> str:
        """
        Handle HUD-level email actions (open_email, summarise_email, search_docs_from_email)
        that operate on the currently focused email.
        """
        if not choices:
            return "I didn't catch which action you wanted, Sir."
        action = choices[0]
        record = getattr(self, "current_email", None) or getattr(self, "_last_email_focus", None)
        if not record:
            return "I don't have an email in focus to work with, Sir."

        subject = record.get("subject") or "that email"

        if action == "open_email":
            await self._activate_email_focus_from_record(question_id, record)
            return f"Focused on {subject}, Sir."

        if action == "summarise_email":
            body = record.get("body") or record.get("snippet") or ""
            if not body:
                return "I don't have enough content from that email to summarise, Sir."
            prompt = (
                "Summarise this email in 2–4 sentences for voice. "
                "Skip unsubscribe links and boilerplate. Focus on key details."
            )
            try:
                completion = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model=self.ai_model,
                    messages=[
                        {"role": "system", "content": prompt},
                        {
                            "role": "user",
                            "content": f"Subject: {subject}\n\n{body}",
                        },
                    ],
                    max_tokens=MAX_CHAT_TOKENS,
                )
                summary = completion.choices[0].message.content or ""
            except Exception as exc:  # noqa: BLE001
                logger.warning("[EmailHUD] Summarisation failed: %s", exc)
                return "I couldn't summarise that email just now, Sir."
            summary_text = summary.strip()
            if not summary_text:
                return "I couldn't summarise that email just now, Sir."
            await self._send_email_context_summary(question_id, summary_text)
            return f"Here's a brief summary of {subject}, Sir."

        if action == "search_docs_from_email":
            return "I haven't wired document search from this email yet, Sir, but the HUD is ready for it."

        return "I couldn't interpret that follow-up action, Sir."

    def _make_email_hud_reply_options(self, question_id: str, topic: str | None = None) -> dict[str, Any]:
        """Shared payload for the email follow-up choices displayed in the HUD."""
        topic_label = topic or f"Email follow-up {question_id[-6:]}"
        choices = [
            {
                "id": "open_email",
                "label": "Open selected email",
                "action": "open_email",
                "query_id": question_id,
            },
            {
                "id": "summarise_email",
                "label": "Summarise this email",
                "action": "summarise_email",
                "query_id": question_id,
            },
            {
                "id": "search_docs_from_email",
                "label": "Search docs for this topic",
                "action": "search_docs_from_email",
                "query_id": question_id,
            },
        ]
        return {
            "type": "followup_choices",
            "question_id": question_id,
            "query_id": question_id,
            "topic": topic_label,
            "choices": choices,
        }

    def _normalize_web_search_result(self, result: dict[str, Any], index: int) -> dict[str, Any]:
        """Prepare HUD-friendly web search entries from the agent results."""
        result_id = result.get("id") or result.get("url") or f"web-{index}"
        title = result.get("title") or "Untitled"
        snippet = (result.get("snippet") or "").strip()
        return {
            "id": result_id,
            "title": title,
            "url": result.get("url") or "",
            "snippet": snippet,
            "source": result.get("source") or "web",
            "metadata": {"position": index},
        }

    async def _activate_web_focus_from_record(self, query_id: str | None, record: dict[str, Any]):
        """Update HUD focus/context panels for the selected web result."""
        if not record:
            return
        self.current_web_result = record
        self._last_web_focus = dict(record)
        focus_text = record.get("snippet") or record.get("title") or ""
        await self._send_focus_panel(query_id, record.get("title") or "Web result", focus_text)
        context_points = []
        url = record.get("url")
        if url:
            context_points.append(f"URL: {url}")
        if focus_text:
            context_points.append(f"Preview: {focus_text}")
        if context_points:
            await self._send_context_panel(query_id, record.get("title") or "Web result", context_points)

    def _make_web_hud_reply_options(self, question_id: str, topic: str | None = None) -> dict[str, Any]:
        """Shared payload for web search follow-up choices sent to the HUD."""
        topic_label = topic or f"Web follow-up {question_id[-6:]}"
        choices = [
            {
                "id": "open_web_result",
                "label": "Open selected result",
                "action": "open_web_result",
                "query_id": question_id,
            },
            {
                "id": "summarise_web_result",
                "label": "Summarise this result",
                "action": "summarise_web_result",
                "query_id": question_id,
            },
            {
                "id": "search_docs_from_web_result",
                "label": "Search docs for this topic",
                "action": "search_docs_from_web_result",
                "query_id": question_id,
            },
        ]
        return {
            "type": "followup_choices",
            "question_id": question_id,
            "query_id": question_id,
            "topic": topic_label,
            "choices": choices,
        }

    def _prune_email_search_history(self):
        """Keep the email search result cache to a reasonable size."""
        while len(self._pending_email_search_results) > MAX_EMAIL_SEARCH_HISTORY:
            self._pending_email_search_results.pop(next(iter(self._pending_email_search_results)), None)

    def _prune_web_search_history(self):
        """Keep the web search result cache to a reasonable size."""
        while len(self._pending_web_search_results) > MAX_WEB_SEARCH_HISTORY:
            self._pending_web_search_results.pop(next(iter(self._pending_web_search_results)), None)

    async def _send_email_reply_options(
        self,
        query_id: str | None,
        email_meta: dict[str, Any],
        topic: str,
        draft: str | None = None,
    ):
        question_id = query_id or self._generate_question_id()
        payload = {
            "type": "followup_choices",
            "question_id": question_id,
            "topic": topic,
            "choices": {"A": "Send reply", "B": "Edit draft", "C": "Discard"},
            "handler": "email_reply_followup",
            "email": {
                "id": email_meta.get("id"),
                "threadId": email_meta.get("threadId"),
                "from": email_meta.get("from"),
                "subject": email_meta.get("subject"),
                "date": email_meta.get("date"),
                "body": email_meta.get("body"),
            },
        }
        if draft:
            payload["draft"] = draft
        self.pending_choices[question_id] = {
            "question_id": question_id,
            "handler": "email_reply_followup",
            "topic": topic,
            "email": payload["email"],
            "draft": draft,
        }
        self._activate_followup(question_id, topic)
        sent = await self._emit_followup_choices(payload, "web_search")
        if sent:
            logger.info("[EmailHUD] Reply options A/B/C sent for query_id=%s", question_id)
        return question_id

    async def _generate_email_draft(self, email_meta: dict[str, Any], instruction: str | None) -> str:
        prompt_instruction = (
            "Draft a concise, polite reply in Jarvis butler style. Keep it short and clear."
        )
        if instruction:
            prompt_instruction += f" User instruction: {instruction}"
        subject = email_meta.get("subject") or "your recent email"
        body = email_meta.get("body") or ""
        messages = [
            {"role": "system", "content": prompt_instruction},
            {
                "role": "user",
                "content": (
                    f"Original email subject: {subject}\n"
                    f"Body:\n{body}\n"
                    "Please craft a calm, professional response."
                ),
            },
        ]
        try:
            completion = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.ai_model,
                messages=messages,
                max_tokens=MAX_CHAT_TOKENS,
            )
            return completion.choices[0].message.content.strip()
        except Exception as exc:
            logger.warning("[EmailDraft] Draft generation failed: %s", exc)
            return ""

    async def _handle_email_edit_instruction(self, instruction: str) -> str:
        context = self.email_edit_context
        if not context:
            return "I don't recall which email draft we're editing, Sir."
        question_id = context.get("question_id")
        email_meta = context.get("email") or {}
        draft = await self._generate_email_draft(email_meta, instruction)
        context["draft"] = draft
        self.pending_choices[question_id] = context
        self.email_edit_context = None
        if question_id in self._pending_email_reply_drafts:
            self._pending_email_reply_drafts[question_id].update({"draft": draft, "email": email_meta})
        await self._send_email_context_draft(question_id, draft)
        topic = context.get("topic") or f"Email: {email_meta.get('subject', '(no subject)')}"
        await self._send_email_reply_options(question_id, email_meta, topic, draft=draft)
        return "Draft updated per your edits, Sir. Choose A to send, B to edit again, or C to discard."

    def _select_recent_messages(self, count: int = 1, unread_only: bool = False) -> list[dict]:
        """Select recent messages as a heuristic target."""
        try:
            from_time = datetime.now(timezone.utc) - timedelta(days=7)
            messages = search_messages_in_window(from_time, None, unread_only=unread_only, max_items=count)
            return messages[:count]
        except Exception as exc:
            logger.error("[EmailSelect] Failed to select recent messages: %s", exc)
            return []

    def _is_email_bulk_risky(self, text: str) -> bool:
        """Detect risky bulk mark-read intents (read/red ambiguity)."""
        if not text:
            return False
        normalized = re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()
        if "mark" not in normalized or "all" not in normalized:
            return False
        if not any(k in normalized for k in ["email", "mail", "inbox", "messages"]):
            return False
        if "read" in normalized or "red" in normalized:
            return True
        return False

    def _parse_followup_option(self, text: str) -> list[str] | None:
        """Parse simple follow-up option selections (e.g., 'Option B', 'B', 'cancel')."""
        if not text:
            return None
        normalized = re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()
        if normalized in {"option a", "a"}:
            return ["A"]
        if normalized in {"option b", "b"}:
            return ["B"]
        if normalized in {"option c", "c", "cancel"}:
            return ["C"]
        return None

    async def _handle_email_bulk_followup(self, payload: dict, choices: list[str]):
        """Handle structured follow-up choices for risky email bulk actions."""
        question_id = payload.get("question_id")
        choice = None
        for ch in choices:
            if ch in ("A", "B", "C"):
                choice = ch
                break
        if not choice:
            return "I didn't catch which option you wanted, Sir."

        # Clear awaiting state for this flow
        self.conversation_state["awaiting_followup"] = False
        self.conversation_state["last_question_id"] = None
        self.pending_choices.pop(question_id, None)

        if choice == "C":
            return "Understood. I won't change any emails, Sir."

        filter_since = None
        filter_label = "all_unread"
        if choice == "B":
            london_tz = ZoneInfo("Europe/London")
            now = datetime.now(london_tz)
            filter_since = now.replace(hour=0, minute=0, second=0, microsecond=0)
            filter_label = "unread_since_today"

        result = await asyncio.to_thread(mark_inbox_unread, filter_since, 500)
        if not isinstance(result, dict):
            return "Email action did not return a structured result, Sir."

        if not result.get("success"):
            err = result.get("error") or "unknown error"
            return f"I couldn't change your emails because Google returned: {err}"

        count = result.get("marked", 0)
        scope = result.get("scope", "inbox")
        return f"I've marked {count} emails as read in your {scope}, Sir."

    async def _handle_email_bulk_risky(self, original_text: str):
        """Emit follow-up choices for risky bulk email commands."""
        question_id = self._generate_question_id()
        topic = "Email bulk action confirmation"
        choices = {
            "A": "Mark all emails as read",
            "B": "Mark only today's unread emails as read",
            "C": "Cancel — do nothing",
        }
        payload = {
            "question_id": question_id,
            "topic": topic,
            "choices": choices,
            "handler": "email_bulk_mark_read",
            "metadata": {"origin_text": original_text},
        }
        self.pending_choices[question_id] = payload
        self._activate_followup(question_id, topic)

        question_text = (
            "You asked me to mark all your emails read. Just to be safe: "
            "A: Mark all emails as read; B: Mark only today's unread emails as read; "
            "C: Cancel."
        )

        payload = {
            "type": "followup_choices",
            "question_id": question_id,
            "topic": topic,
            "choices": choices,
        }
        try:
            if hasattr(self, "hud_event_sink") and callable(self.hud_event_sink):
                await self._emit_followup_choices(payload, "email")
                logger.info("[FOLLOWUP] Sent followup_choices event for question_id=%s (email bulk)", question_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[FOLLOWUP] Failed to send followup_choices event: %s", exc)

        return question_text

    async def _handle_calendar_delete_followup(self, payload: dict, choices: list[str]):
        """Handle follow-up choices for calendar delete confirmation."""
        event = payload.get("event") or {}
        event_id = event.get("id")
        summary = event.get("summary", "the event")
        start = event.get("start", {}) or {}
        when = start.get("date") or start.get("dateTime") or "the scheduled time"
        choice = None
        for ch in choices:
            if ch in ("A", "B", "C"):
                choice = ch
                break
        if not choice:
            return "I didn't catch which option you wanted, Sir."
        if choice == "C":
            return "Understood, I'll leave it as it is, Sir."
        if choice == "B":
            return "I haven't implemented rescheduling via this path yet, Sir; the event is unchanged."
        # choice == "A"
        try:
            result = await asyncio.to_thread(calendar_delete_event, event_id)
            if result.get("success"):
                return f"I've cancelled '{summary}' on {when}, Sir."
            err = result.get("details", {}).get("error") if isinstance(result, dict) else "unknown error"
            return f"I couldn't cancel that event because Google returned: {err}"
        except Exception as exc:
            logger.error("[CalendarAction] delete_event failed: %s", exc)
            return f"I couldn't cancel that event: {exc}"

    def _parse_email_send(self, text: str) -> dict | None:
        """Very simple parser for send email intent."""
        lower = text.lower()
        to = None
        subject = None
        body = None
        if "email " in lower:
            after = text.split("email ", 1)[1]
        elif "send an email to " in lower:
            after = text.split("send an email to ", 1)[1]
        else:
            return None
        if " about " in after.lower():
            parts = re.split(r"about", after, flags=re.IGNORECASE, maxsplit=1)
            to = parts[0].strip(" ,.")
            body = parts[1].strip() if len(parts) > 1 else ""
            subject = body[:60] if body else "No subject"
        elif " saying " in after.lower():
            parts = re.split(r"saying", after, flags=re.IGNORECASE, maxsplit=1)
            to = parts[0].strip(" ,.")
            body = parts[1].strip() if len(parts) > 1 else ""
            subject = body[:60] if body else "No subject"
        else:
            to = after.strip(" ,.")
            subject = "No subject"
            body = ""
        if not to:
            return None
        return {"to": to, "subject": subject or "No subject", "body": body or ""}

    def _extract_count(self, text: str, default: int = 1) -> int:
        match = re.search(r"last\s+(\d+)", text.lower())
        if match:
            try:
                return max(1, int(match.group(1)))
            except Exception:
                return default
        return default

    async def _handle_email_send(self, text: str):
        parsed = self._parse_email_send(text)
        if not parsed:
            return "I couldn't parse the recipient or message, Sir."
        try:
            result = await asyncio.to_thread(
                send_email, parsed["to"], parsed["subject"], parsed["body"], None, None
            )
            if result.get("success"):
                return f"Email sent to {parsed['to']} with subject '{parsed['subject']}', Sir."
            err = result.get("details", {}).get("error") if isinstance(result, dict) else "unknown error"
            return f"I couldn't send that email because: {err}"
        except Exception as exc:
            logger.error("[EmailAction] send_email failed: %s", exc)
            return f"I couldn't send that email: {exc}"

    async def _handle_email_mark_read(self, text: str):
        count = self._extract_count(text, default=1)
        messages = self._select_recent_messages(count, unread_only=False)
        ids = [m.get("id") for m in messages if m.get("id")]
        if not ids:
            return "I couldn't find messages to mark as read, Sir."
        result = await asyncio.to_thread(mark_messages_read_action, ids)
        if result.get("success"):
            return f"I've marked {len(ids)} message(s) as read, Sir."
        err = result.get("details", {}).get("error") if isinstance(result, dict) else "unknown error"
        return f"I couldn't mark messages as read because: {err}"

    async def _handle_email_mark_unread(self, text: str):
        count = self._extract_count(text, default=1)
        messages = self._select_recent_messages(count, unread_only=False)
        ids = [m.get("id") for m in messages if m.get("id")]
        if not ids:
            return "I couldn't find messages to mark as unread, Sir."
        result = await asyncio.to_thread(mark_messages_unread, ids)
        if result.get("success"):
            return f"I've marked {len(ids)} message(s) as unread, Sir."
        err = result.get("details", {}).get("error") if isinstance(result, dict) else "unknown error"
        return f"I couldn't mark messages as unread because: {err}"

    async def _handle_email_archive(self, text: str):
        count = self._extract_count(text, default=1)
        messages = self._select_recent_messages(count, unread_only=False)
        ids = [m.get("id") for m in messages if m.get("id")]
        if not ids:
            return "I couldn't find messages to archive, Sir."
        result = await asyncio.to_thread(archive_messages, ids)
        if result.get("success"):
            return f"I've archived {len(ids)} message(s), Sir."
        err = result.get("details", {}).get("error") if isinstance(result, dict) else "unknown error"
        return f"I couldn't archive messages because: {err}"

    async def _handle_email_apply_label(self, text: str):
        count = self._extract_count(text, default=1)
        label_match = re.search(r"label (.+)", text, flags=re.IGNORECASE)
        label = label_match.group(1).strip() if label_match else "Label"
        messages = self._select_recent_messages(count, unread_only=False)
        ids = [m.get("id") for m in messages if m.get("id")]
        if not ids:
            return "I couldn't find messages to label, Sir."
        result = await asyncio.to_thread(apply_label, ids, label)
        if result.get("success"):
            return f"I've applied label '{label}' to {len(ids)} message(s), Sir."
        err = result.get("details", {}).get("error") if isinstance(result, dict) else "unknown error"
        return f"I couldn't apply the label because: {err}"

    async def _handle_email_delete(self, text: str):
        count = self._extract_count(text, default=1)
        messages = self._select_recent_messages(count, unread_only=False)
        ids = [m.get("id") for m in messages if m.get("id")]
        if not ids:
            return "I couldn't find messages to delete, Sir."
        question_id = self._generate_question_id()
        self.pending_choices[question_id] = {
            "question_id": question_id,
            "handler": "email_delete",
            "message_ids": ids,
        }
        topic = "Email delete confirmation"
        self._activate_followup(question_id, topic)
        prompt = f"Do you want me to delete {len(ids)} message(s), Sir? A: Yes, delete. B: No change. C: Cancel."
        payload = {
            "type": "followup_choices",
            "question_id": question_id,
            "topic": topic,
            "choices": {"A": "Delete", "B": "Leave unchanged", "C": "Cancel"},
        }
        try:
            if hasattr(self, "hud_event_sink") and callable(self.hud_event_sink):
                await self._emit_followup_choices(payload, "email")
                logger.info("[EmailConfirm] Sent followup_choices question_id=%s", question_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[EmailConfirm] Failed to send HUD event: %s", exc)
        return prompt

    async def _handle_email_delete_followup(self, payload: dict, choices: list[str]):
        ids = payload.get("message_ids") or []
        if not ids:
            return "No messages were selected for deletion, Sir."
        choice = None
        for ch in choices:
            if ch in ("A", "B", "C"):
                choice = ch
                break
        if not choice or choice == "C":
            return "Understood, I won't delete any emails, Sir."
        if choice == "B":
            return "Leaving the emails unchanged, Sir."
        # A: delete
        try:
            result = await asyncio.to_thread(delete_messages, ids)
            if result.get("success"):
                return f"I've deleted {len(ids)} message(s), Sir."
            err = result.get("details", {}).get("error") if isinstance(result, dict) else "unknown error"
            return f"I couldn't delete those emails because: {err}"
        except Exception as exc:
            logger.error("[EmailAction] delete_messages failed: %s", exc)
            return f"I couldn't delete those emails: {exc}"

    async def _handle_email_search(self, text: str, query: str | None = None, fuzzy_allowed: bool = False):
        """Handle email search intents via EmailAgent."""
        search_query = (query or "").strip() or text
        logger.info("[EmailSearch] Detected email search query='%s' fuzzy_allowed=%s", search_query, fuzzy_allowed)
        intent = {
            "domain": "email",
            "action": "search_emails_by_query",
            "query": search_query,
            "max_results": 20,
            "fuzzy_allowed": fuzzy_allowed,
        }
        try:
            result = await asyncio.to_thread(self.email_agent.execute, intent)
        except Exception as exc:  # noqa: BLE001
            logger.error("[EmailSearch] EmailAgent failed: %s", exc)
            return "I couldn't access your email right now, Sir."

        if not isinstance(result, dict):
            logger.warning("[EmailSearch] Unexpected result type: %s", type(result))
            return "I couldn't access your email right now, Sir."

        messages = (result.get("data") or {}).get("messages") or []
        success = result.get("success") or result.get("status") == "ok"
        if not success:
            err = result.get("error") or result.get("message") or "unknown error"
            logger.warning("[EmailSearch] search_emails_by_query failed: %s", err)
            return "I couldn't search your email right now, Sir."

        hud_sent = False
        question_id = self._generate_question_id()
        normalized_messages = [self._normalize_email_search_result(msg) for msg in messages]
        if normalized_messages:
            self._pending_email_search_results[question_id] = normalized_messages
            self._prune_email_search_history()
        try:
            # For topic=email.search the HUD expects a list of email results, not A/B/C options.
            payload = {
                "type": "updateReplyOptions",
                "question_id": question_id,
                "topic": "email.search",
                "choices": normalized_messages,
            }
            hud_sent = await self._emit_hud_event(payload)
            if normalized_messages:
                followup_topic = f"Email search: {self._preview_text(search_query, 60)}"
                reply_payload = self._make_email_hud_reply_options(question_id, topic=followup_topic)
                await self._emit_followup_choices(reply_payload, "email")
                self._activate_followup(question_id, followup_topic)
                logger.info(
                    "[EmailHUD] Prepared %d results with follow-up choices for question_id=%s",
                    len(normalized_messages),
                    question_id,
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("[EmailSearch] Failed to send HUD payload: %s", exc)

        if messages:
            if hud_sent:
                return f"I found {len(messages)} email(s) matching your search. Check the HUD for details, Sir."
            return f"I found {len(messages)} email(s) matching your search, but I couldn't update the HUD, Sir."
        if hud_sent:
            return "I didn't find any matching emails, Sir."
        return "I didn't find any matching emails, and I couldn't update the HUD, Sir."

    def save_system_summary(self, text: str) -> str:
        """
        Controlled helper to save a system summary/health note via the file service.
        """
        if not self.file_service or not self.file_service.is_enabled:
            return "FileService disabled: set JARVIS_VAULT_PATH to enable saving."

        result = self.file_service.create_file(
            name="system_check",
            ext="md",
            category="system",
            content=text
        )

        if result.get("success"):
            return f"System summary saved: {result.get('full_path')}"

        return f"Save failed: {result.get('message', 'unknown error')}"
    
    def init_brain_system(self):
        """Initialize the JARVIS brain system"""
        try:
            print(f"­ƒôì Location: {self.location_name}")
            print(f"­ƒÆ╗ System: {self.system_info['platform']}")
            print(f"­ƒûÑ´©Å  Hostname: {self.system_info['hostname']}")
            print(f"ÔÜí CPU Cores: {self.system_info['cores']}")
            print(f"­ƒÆ¥ Total RAM: {self.system_info['memory_total']} GB")
            
            if self.system_info['gpu_available']:
                print(f"­ƒÄ« GPU: {self.system_info['gpu_available']}")
            else:
                print("ÔÜá´©Å  GPU: Not detected")
            
            print("")
            print("­ƒöº Initializing AI components...")
            
            # Initialize Ollama (local LLM) + OpenAI (TTS only)
            self.openai_client = OpenAI(
                base_url=self.llm_base_url or 'http://localhost:11434/v1',
                api_key=self.llm_api_key or 'ollama'  # Local requires no real key
            )
            print(f"Ô£à LLM profile '{self.llm_profile}' initialized using model {self.ai_model}")
            
            # Separate OpenAI client for TTS (keeps fable voice)
            self.tts_client = OpenAI()
            print("Ô£à OpenAI TTS initialized (fable voice)")
            
            # Initialize JARVIS personality framework
            print("­ƒÄ¡ Loading JARVIS personality framework...")
            self.personality_engine = PersonalityEngine()
            print("   Ô£ô Personality engine loaded")
            
            memory_path = os.getenv("JARVIS_MEMORY_PATH", "/root/JARVIS/runtime/memory_v2")
            self.memory = JARVISMemory(persist_directory=os.path.expanduser(memory_path))
            print(f"   Ô£ô Memory system loaded ({os.path.expanduser(memory_path)})")
            
            self.context_manager = ContextManager(memory_system=self.memory, max_memories=3)
            print("   Ô£ô Context manager loaded")
            
            self.proactive_engine = ProactiveSuggestionEngine()
            self._init_agents()
            print("   Ô£ô Proactive engine loaded")
            
            print("")
            print("=" * 60)
            print("Ô£à JARVIS BRAIN ONLINE - Ready for commands")
            print("=" * 60)
            print("")
            
        except Exception as e:
            print(f"ÔØî Initialization error: {e}")
            raise

    def _init_agents(self):
        """Instantiate the domain agents that drive the router logic."""
        self.web_search_agent = WebSearchAgent(
            llm_client=self.openai_client,
            file_service=self.file_service,
            memory=self.memory,
        )
        self.memory_agent = MemoryAgent(memory_system=self.memory, file_service=self.file_service)
        self.calendar_agent = CalendarAgent(file_service=self.file_service)
        self.docs_agent = DocsAgent(llm_client=self.openai_client, file_service=self.file_service)
        self.local_docs_agent = LocalDocsSearchAgent(file_service=self.file_service)
        self.system_agent = SystemAgent(system_info=self.system_info)
        self.agent_registry = {
            self.web_search_agent.DOMAIN: self.web_search_agent,
            self.memory_agent.DOMAIN: self.memory_agent,
            self.calendar_agent.DOMAIN: self.calendar_agent,
            self.docs_agent.DOMAIN: self.docs_agent,
            self.local_docs_agent.DOMAIN: self.local_docs_agent,
            self.system_agent.DOMAIN: self.system_agent,
        }
    
    def _is_time_query(self, text):
        """
        Detect if user is asking for the current time
        Simple pattern matching - no ML needed
        """
        normalized = text.lower().strip()
        # Remove common punctuation
        normalized = re.sub(r'[?!.,]', '', normalized)
        
        time_patterns = [
            r'\bwhat(s|\s+is)\s+the\s+time\b',
            r'\bwhat\s+time\s+is\s+it\b',
            r'\btell\s+me\s+the\s+time\b',
            r'\bcan\s+you\s+tell\s+me\s+the\s+time\b',
            r'\bwhats\s+the\s+time\b',
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, normalized):
                return True
        return False
    
    def _get_current_time_response(self):
        """
        Get current time in Europe/London timezone
        Returns natural language response in JARVIS voice
        """
        try:
            # Get current time in London timezone
            london_tz = ZoneInfo("Europe/London")
            now = datetime.now(london_tz)
            
            # Format time naturally
            time_str = now.strftime("%I:%M %p").lstrip('0').lower()
            # Remove leading zero from hour if present
            
            response = f"The current time in {self.location_name} is {time_str}, Sir."
            
            print(f"ÔÅ░ TIME_INTENT detected - Local time: {now.isoformat()}")
            print(f"ÔÅ░ Spoken response: {response}")
            
            return response, now
            
        except Exception as e:
            print(f"ÔØî Error getting time: {e}")
            # Fallback to system time
            now = datetime.now()
            time_str = now.strftime("%I:%M %p").lstrip('0').lower()
            return f"The time is {time_str}, Sir.", now

    def _extract_search_query(self, text: str) -> str | None:
        """Extract a web search query from supported command phrases."""
        normalized = (text or "").strip()
        lower = normalized.lower()

        if lower.startswith("!search"):
            query = normalized[len("!search"):].strip()
            return query or None

        patterns = [
            r"search the web for\s+(?P<query>.+)",
            r"jarvis,\s*search the web for\s+(?P<query>.+)",
            r"jarvis,\s*look up\s+(?P<query>.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match:
                candidate = match.group("query").strip()
                return candidate or None
        if AstraMeaningNormalizer.looks_like_web_query(normalized):
            return normalized or None
        return None

    @staticmethod
    def _slugify_query(query: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", (query or "").lower()).strip("-")
        slug = re.sub(r"-{2,}", "-", slug)
        return slug or "web-search"

    @staticmethod
    @staticmethod
    def _is_email_intent(text: str) -> bool:
        lower = (text or "").lower()
        normalized = re.sub(r"[^a-z0-9]+", " ", lower).strip()
        patterns = [
            r"jarvis\s+summari[sz]e\s+my\s+new\s+e\s?mails",
            r"summari[sz]e\s+my\s+e\s?mails",
            r"summari[sz]e\s+my\s+inbox",
            r"summari[sz]e\s+my\s+unread\s+e\s?mails",
            r"give\s+me\s+an\s+email\s+summary",
        ]
        return any(re.search(p, normalized) for p in patterns)

    @staticmethod
    def _is_email_search_intent(text: str) -> bool:
        normalized = re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower()).strip()
        if not normalized:
            return False
        search_terms = ["search", "find", "look for", "look up", "scan for", "look in", "look through"]
        email_terms = ["email", "emails", "inbox", "mail", "messages", "gmail"]
        has_search = any(term in normalized for term in search_terms)
        has_email = any(term in normalized for term in email_terms)
        return has_search and has_email

    @staticmethod
    def _is_mark_read_intent(text: str) -> bool:
        normalized = re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()
        if "mark" not in normalized or "read" not in normalized:
            return False
        keywords = ("email", "e mail", "inbox", "mail", "messages")
        return any(k in normalized for k in keywords)

    @staticmethod
    def _is_email_read_intent(text: str) -> bool:
        normalized = re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()
        if "read" not in normalized:
            return False
        return "email" in normalized or "mail" in normalized

    @staticmethod
    def _is_reply_intent(text: str) -> bool:
        normalized = re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()
        return "reply" in normalized and ("email" in normalized or "that" in normalized or "it" in normalized)

    @staticmethod
    def _is_email_summary_recall_intent(text: str) -> bool:
        normalized = (text or "").lower()
        return "email summary" in normalized or "email brief" in normalized or "summary you saved" in normalized

    @staticmethod
    def _is_confirmation(text: str) -> bool:
        normalized = (text or "").strip().lower()
        return normalized in {"yes", "yeah", "yep", "confirm", "do it", "go ahead", "sure"} or normalized.startswith(
            "yes"
        )

    @staticmethod
    def _is_decline(text: str) -> bool:
        normalized = (text or "").strip().lower()
        return normalized in {"no", "nope", "cancel", "stop", "never mind"} or normalized.startswith("no ")

    def _resolve_mark_read_window(self, text: str):
        """Resolve a time window from the user text."""
        london_tz = ZoneInfo("Europe/London")
        now = datetime.now(london_tz)
        lower = (text or "").lower()

        if "last summary" in lower:
            latest = get_latest_library_item("email", filter_tags=["summary", "daily"]) or get_latest_library_item(
                "email"
            )
            if latest and latest.get("timestamp"):
                try:
                    start = datetime.fromisoformat(latest["timestamp"]).astimezone(london_tz)
                    logger.info("[EmailMarkRead] Using last summary time as start: %s", start.isoformat())
                    return {"from": start, "to": now, "source": "last_summary"}
                except Exception:
                    logger.warning("[EmailMarkRead] Failed to parse last summary timestamp: %s", latest.get("timestamp"))

        time_match = re.search(r"since\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            ampm = time_match.group(3)
            if ampm:
                if ampm == "pm" and hour != 12:
                    hour += 12
                if ampm == "am" and hour == 12:
                    hour = 0
            start = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            logger.info("[EmailMarkRead] Parsed explicit time window start: %s", start.isoformat())
            return {"from": start, "to": now, "source": "explicit_time"}

        if "afternoon" in lower:
            start = now.replace(hour=12, minute=0, second=0, microsecond=0)
            logger.info("[EmailMarkRead] Defaulting to afternoon (12:00) start")
            return {"from": start, "to": now, "source": "afternoon", "needs_confirmation": True}

        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        logger.info("[EmailMarkRead] Defaulting to start of day window")
        return {"from": start_of_day, "to": now, "source": "start_of_day"}

    def _parse_email_read_request(self, text: str) -> dict:
        lower = (text or "").lower()
        sender = None
        topic = None
        if "from " in lower:
            sender = lower.split("from ", 1)[1].split(" about")[0].split(" regarding")[0].strip()
        if "about " in lower:
            topic = lower.split("about ", 1)[1].strip()
        if "email about" in lower and not topic:
            topic = lower.split("email about", 1)[1].strip()
        if "email from" in lower and not sender:
            sender = lower.split("email from", 1)[1].strip()
        return {"sender": sender, "topic": topic}

    def _resolve_summary_date(self, text: str) -> str | None:
        lower = (text or "").lower()
        london_tz = ZoneInfo("Europe/London")
        today = datetime.now(london_tz).date()
        if "today" in lower:
            return today.isoformat()
        if "yesterday" in lower:
            return (today - timedelta(days=1)).isoformat()
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for idx, name in enumerate(weekdays):
            if name in lower:
                # Find most recent occurrence in last 7 days including today
                days_ago = (today.weekday() - idx) % 7
                if days_ago == 0:
                    days_ago = 7
                target = today - timedelta(days=days_ago)
                return target.isoformat()
        return today.isoformat()

    @staticmethod
    def _calendar_intent(text: str) -> str | None:
        lower = (text or "").lower()
        normalized = re.sub(r"[^a-z0-9]+", " ", lower).strip()
        keywords = ["calendar", "schedule", "agenda", "appointments", "meetings", "events"]
        has_keyword = any(k in normalized for k in keywords)
        if not has_keyword:
            return None

        if "tomorrow" in normalized or "next day" in normalized:
            return "tomorrow"
        if "today" in normalized or "tonight" in normalized:
            return "today"
        if "week" in normalized:
            return "week"
        if "next important" in normalized or "next event" in normalized:
            return "next"
        return None

    def _is_calendar_add_event(self, text: str) -> bool:
        """Detect add/create/schedule calendar event intents."""
        if not text:
            return False
        normalized = re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()
        keywords = ["add", "create", "schedule", "set up", "book"]
        nouns = ["meeting", "event", "appointment", "calendar"]
        if any(k in normalized for k in keywords) and any(n in normalized for n in nouns):
            return True
        return False

    def _detect_calendar_intent(self, text: str) -> str | None:
        if self._is_calendar_add_event(text):
            return "calendar_add_event"
        lower = (text or "").lower()
        if any(k in lower for k in ["move", "reschedule", "shift", "update"]) and any(
            w in lower for w in ["meeting", "event", "appointment", "calendar"]
        ):
            return "calendar_update_event"
        if any(k in lower for k in ["cancel", "delete", "remove"]) and any(
            w in lower for w in ["meeting", "event", "appointment", "calendar"]
        ):
            return "calendar_delete_event"
        return None

    def _detect_email_intent(self, text: str) -> str | None:
        normalized = re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower()).strip()
        if any(k in normalized for k in ["send", "email"]) and "subject" in normalized or normalized.startswith("email "):
            return "email_send"
        if "mark" in normalized and "unread" in normalized:
            return "email_mark_unread"
        if "mark" in normalized and "read" in normalized:
            return "email_mark_read"
        if "archive" in normalized:
            return "email_archive"
        if "label" in normalized:
            return "email_apply_label"
        if "delete" in normalized or "remove" in normalized:
            return "email_delete"
        return None

    def _parse_calendar_add_spec(self, text: str) -> dict:
        """Lightweight parser for calendar event creation."""
        lower = text.lower()
        london_tz = ZoneInfo("Europe/London")
        now = datetime.now(london_tz)

        # Date resolution
        date = now.date()
        if "tomorrow" in lower:
            date = date + timedelta(days=1)
        else:
            weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for idx, name in enumerate(weekdays):
                if name in lower:
                    today_idx = now.weekday()
                    target_idx = idx
                    days_ahead = (target_idx - today_idx) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    date = date + timedelta(days=days_ahead)
                    break

        # Time parsing
        time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", lower)
        start_dt = None
        end_dt = None
        all_day = False
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            ampm = time_match.group(3)
            if ampm:
                if ampm == "pm" and hour != 12:
                    hour += 12
                if ampm == "am" and hour == 12:
                    hour = 0
            start_dt = datetime(date.year, date.month, date.day, hour, minute, tzinfo=london_tz)
            end_dt = start_dt + timedelta(minutes=60)
        else:
            all_day = True
            start_dt = datetime(date.year, date.month, date.day, 0, 0, tzinfo=london_tz)
            end_dt = start_dt + timedelta(days=1)

        # Title extraction
        title = text.strip()
        for marker in ["called", "titled", "named"]:
            if marker in lower:
                idx = lower.find(marker)
                title = text[idx + len(marker):].strip(" :\"'") or title
                break
        # Trim directive phrases
        title = re.sub(
            r"\b(add|create|schedule|set up|put|appointment|meeting|event|calendar)\b",
            "",
            title,
            flags=re.IGNORECASE,
        ).strip(" ,.-")
        if not title or len(title.split()) < 2:
            # fallback: use remaining nouns
            tokens = [t for t in re.split(r"\s+", text) if t.lower() not in {"add", "create", "schedule", "meeting", "event", "appointment", "calendar", "at", "on", "for", "set"}]
            title = " ".join(tokens).strip() or "New event"

        return {
            "title": title,
            "start": start_dt,
            "end": end_dt,
            "all_day": all_day,
            "description": f"Created by Jarvis from: {text}",
            "location": None,
            "timezone": "Europe/London",
        }

    def _build_web_results_markdown(self, query: str, summary: str, results: list[dict], timestamp: datetime) -> str:
        lines = [
            f'# Web Search: "{query}"',
            "",
            f"**Timestamp:** {timestamp.isoformat()}  ",
            "**Category:** web  ",
            "**Source:** Jarvis WebSearch v1  ",
            "**Context:** voice or text request from Sir",
            "",
            "## Summary",
            summary or "Summary unavailable.",
            "",
            "## Results",
        ]

        if results:
            for idx, item in enumerate(results, start=1):
                title = item.get("title", "Untitled")
                url = item.get("url", "")
                snippet = item.get("snippet", "").strip()
                lines.append(f"{idx}. [{title}]({url})  ")
                if snippet:
                    lines.append(f"   {snippet}")
                lines.append("")
        else:
            lines.append("No results available.")

        return "\n".join(lines).rstrip() + "\n"

    def _write_web_search_to_vault(self, query: str, summary: str, results: list[dict], timestamp: datetime):
        if not self.file_service or not self.file_service.is_enabled:
            logger.info("FileService disabled; skipping web search vault write.")
            return None

        slug = self._slugify_query(query)
        name = f"{timestamp.strftime('%H%M')}_{slug}"
        content = self._build_web_results_markdown(query, summary, results, timestamp)
        result = self.file_service.create_file(
            name=name,
            ext="md",
            category="web",
            content=content,
            allow_overwrite=False,
        )
        if result.get("success"):
            return result.get("full_path")

        logger.warning("Failed to write web search log: %s", result.get("message"))
        return None

    def _store_web_memory(self, query: str, summary: str, timestamp: datetime):
        if not self.memory:
            return None
        text = f"Web search for '{query}' at {timestamp.isoformat()} — summary: {summary}"
        metadata = {
            "type": "conversation",
            "category": "web",
            "source": "web_search",
            "timestamp": timestamp.isoformat(),
            "context": f"query={query}",
        }
        return self.memory.add_conversation_memory(text=text, metadata=metadata)

    async def _handle_web_search(self, query: str, query_id: str | None = None):
        intent = {"domain": WebSearchAgent.DOMAIN, "action": "search", "search_term": query}
        response = await self._route_agent_intent(intent, query, query_id=query_id, return_response=True)
        if not isinstance(response, dict):
            logger.warning("[WebSearch] Unexpected response type: %s", type(response))
            return "I couldn't search the web right now, Sir."

        results = response.get("results") or []
        question_id = query_id or self._generate_question_id()
        normalized_results = [
            self._normalize_web_search_result(item, idx)
            for idx, item in enumerate(results, start=1)
        ]
        if normalized_results:
            self._pending_web_search_results[question_id] = normalized_results
            self._prune_web_search_history()

        try:
            await self._handle_web_search_hud(intent, response, query_id=question_id, send_choices=False)
            if normalized_results:
                payload = {
                    "type": "updateReplyOptions",
                    "question_id": question_id,
                    "topic": "web.search",
                    "choices": normalized_results,
                }
                await self._emit_hud_event(payload)
                followup_topic = response.get("metadata", {}).get("title") or f"Web search: {self._preview_text(query, 60)}"
                reply_payload = self._make_web_hud_reply_options(question_id, topic=followup_topic)
                await self._emit_followup_choices(reply_payload, "web_search")
                self._activate_followup(question_id, followup_topic)
                logger.info(
                    "[WebHUD] Prepared %d results with follow-up choices for question_id=%s",
                    len(normalized_results),
                    question_id,
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("[WebSearch] HUD emit failed: %s", exc)

        fallback_unclear = (
            "I'm not able to get a reliable answer from the web right now, Sir. "
            "Would you like me to open the top search page in the HUD instead?"
        )
        snippets_available = any(item.get("snippet") for item in normalized_results)
        if not normalized_results or not snippets_available:
            return fallback_unclear

        grounded_speech = await self._generate_grounded_web_speech(query, normalized_results)
        if grounded_speech:
            return grounded_speech
        return fallback_unclear

    async def _generate_grounded_web_speech(self, query: str, results: list[dict[str, Any]]) -> str | None:
        """Summarise web search snippets while strictly relying on the provided data."""
        snippet_entries = []
        for idx, item in enumerate(results[:3], start=1):
            title = item.get("title") or f"Result {idx}"
            snippet = item.get("snippet") or ""
            url = item.get("url") or ""
            snippet_entries.append(
                f"- Title: {title}\n  Snippet: {snippet}\n  URL: {url}"
            )
        if not snippet_entries:
            return None

        system_prompt = (
            "You are Jarvis, summarising web search results for Sir. "
            "Use ONLY the information contained in the provided snippets. "
            "If the snippets do not clearly answer the question, say that you're not sure "
            "and suggest checking the HUD links instead of guessing. "
            "Do not invent or guess numbers, dates, or statistics."
        )
        user_prompt = (
            f"Original question: {query!r}\n\n"
            "Here are web search snippets:\n" + "\n".join(snippet_entries)
        )
        try:
            completion = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=MAX_CHAT_TOKENS,
            )
            summary = completion.choices[0].message.content or ""
            return summary.strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning("[WebHUD] Grounded summary failed: %s", exc)
            return None

    async def _handle_web_search_hud(
        self,
        intent: Dict[str, Any],
        response: Dict[str, Any],
        query_id: str | None,
        send_choices: bool = True,
        style: str | None = None,
    ):
        focus_text = response.get("focus_text")
        context_points = response.get("context_points") or []
        web_query = (intent.get("search_term") or response.get("query") or "").strip()
        topic = response.get("metadata", {}).get("title") or f"Web search: {self._preview_text(web_query, 60)}"
        resolved_style = style or response.get("style") or "standard"
        await self._send_focus_panel(query_id, web_query, focus_text)
        await self._send_context_panel(query_id, web_query, context_points)
        if send_choices:
            await self._send_web_reply_options(query_id, web_query, topic, resolved_style)
        else:
            self._schedule_web_reply_options(query_id, web_query, topic, resolved_style)

    async def _handle_web_search_followup(self, payload: dict, choices: list[str]):
        question_id = payload.get("question_id")
        query = (payload.get("query") or "").strip()
        if not query:
            return "I couldn't find the original web query to follow up on, Sir."
        self.pending_choices.pop(question_id, None)
        choice = next((ch for ch in choices if ch in ("A", "B", "C")), None)
        if not choice:
            return "I didn't catch which option you wanted, Sir."
        logger.info("[WebHUD] Followup choice received: %s", choice)
        style_map = {"A": "deeper", "B": "angle", "C": "recap"}
        style = style_map.get(choice, "standard")
        intent = {
            "domain": WebSearchAgent.DOMAIN,
            "action": "search",
            "search_term": query,
            "parameters": {"style": style},
        }
        response = await self._route_agent_intent(intent, query, query_id=question_id, return_response=True)
        await self._handle_web_search_hud(intent, response, query_id=question_id, send_choices=False, style=style)
        topic = payload.get("topic") or f"Web search: {self._preview_text(query, 60)}"
        self._schedule_web_reply_options(question_id, query, topic, style)
        return response.get("speech") or "Here's the updated web search context, Sir."

    async def _handle_web_search_selection(self, question_id: str, choices: list[str]) -> str:
        """Process a web result selection coming from the HUD."""
        results = self._pending_web_search_results.get(question_id, [])
        if not results:
            return "I couldn't find that web result, Sir."
        selected_id = next((choice for choice in choices if choice), None)
        if not selected_id:
            return "I didn't catch which result you selected, Sir."
        selected = next((item for item in results if str(item.get("id")) == str(selected_id)), None)
        if not selected:
            logger.warning(
                "[WebHUD] Selection id=%s not in cached results for question_id=%s",
                selected_id,
                question_id,
            )
            return "That web result is no longer available, Sir."
        await self._activate_web_focus_from_record(question_id, selected)
        title = selected.get("title") or "that web result"
        return f"Focused on {title}, Sir."

    async def _handle_web_hud_followup(self, question_id: str, choices: list[str]) -> str:
        """Handle HUD-level web actions (open/summarise/search docs) on the focused result."""
        if not choices:
            return "I didn't catch which action you wanted, Sir."
        action = choices[0]
        record = getattr(self, "current_web_result", None) or getattr(self, "_last_web_focus", None)
        if not record:
            return "I don't have a web result in focus to work with, Sir."

        title = record.get("title") or "that web result"

        if action == "open_web_result":
            await self._activate_web_focus_from_record(question_id, record)
            url = record.get("url")
            if url:
                return f"Focused on {title}. URL: {url}"
            return f"Focused on {title}, Sir."

        if action == "summarise_web_result":
            snippet = record.get("snippet") or ""
            if not snippet:
                return "I don't have enough information from that result to summarise, Sir."
            prompt = (
                "Summarise this web search result in 2-3 sentences suitable for voice. "
                "Mention the main page title and why it might be useful."
            )
            try:
                completion = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model=self.ai_model,
                    messages=[
                        {"role": "system", "content": prompt},
                        {
                            "role": "user",
                            "content": (
                                f"Title: {title}\n"
                                f"URL: {record.get('url', '')}\n\n"
                                f"{snippet}"
                            ),
                        },
                    ],
                    max_tokens=MAX_CHAT_TOKENS,
                )
                summary = completion.choices[0].message.content or ""
            except Exception as exc:  # noqa: BLE001
                logger.warning("[WebHUD] Summarisation failed: %s", exc)
                return "I couldn't summarise that web result just now, Sir."
            summary_text = summary.strip()
            if not summary_text:
                return "I couldn't summarise that web result just now, Sir."
            await self._send_context_panel(question_id, title, [summary_text])
            return f"Here's a brief summary of {title}, Sir."

        if action == "search_docs_from_web_result":
            return "I haven't wired document search from this web result yet, Sir, but the HUD is ready for it."

        return "I couldn't interpret that follow-up action, Sir."

    async def _handle_email_search_selection(self, question_id: str, choices: list[str]) -> str:
        """Process an email result selection coming from the HUD."""
        results = self._pending_email_search_results.get(question_id, [])
        if not results:
            return "I couldn't find that email result, Sir."
        selected_id = next((choice for choice in choices if choice), None)
        if not selected_id:
            return "I didn't catch which email you selected, Sir."
        selected = next((item for item in results if str(item.get("id")) == str(selected_id)), None)
        if not selected:
            logger.warning(
                "[EmailHUD] Selection id=%s not in cached results for query_id=%s",
                selected_id,
                question_id,
            )
            return "That email is no longer available, Sir."
        message_id = selected.get("id")
        if not message_id:
            return "That email result lacks an identifier, Sir."
        try:
            fetched = await asyncio.to_thread(fetch_full_message, message_id)
        except FileNotFoundError:
            return "Email access is not configured (missing Gmail token)."
        except Exception as exc:
            logger.warning("[EmailSearch] Failed to fetch full message id=%s: %s", message_id, exc)
            fallback_meta = {
                "id": selected.get("id"),
                "threadId": selected.get("threadId") or selected.get("thread_id"),
                "from": selected.get("from"),
                "subject": selected.get("subject"),
                "date": selected.get("date"),
                "snippet": selected.get("snippet"),
                "body": selected.get("body") or selected.get("snippet") or "",
            }
            fallback_record = self._build_email_focus_record(fallback_meta, fallback_meta.get("body"))
            await self._activate_email_focus_from_record(question_id, fallback_record)
            logger.info("[EmailHUD] Focus set from search for query_id=%s id=%s [partial data]", question_id, selected_id)
            return "Focused on that email, Sir, though I could not load the full contents."
        if isinstance(fetched, tuple) and len(fetched) >= 2:
            meta, body = fetched[0], fetched[1]
        elif isinstance(fetched, dict):
            meta, body = fetched, fetched.get("body", "")
        else:
            return "I couldn't interpret that email, Sir."
        focus_record = self._build_email_focus_record(meta, body)
        await self._activate_email_focus_from_record(question_id, focus_record)
        logger.info("[EmailHUD] Focus set from search for query_id=%s id=%s", question_id, selected_id)
        return f"Focused on {focus_record.get('subject','that email')}, Sir."

    async def _handle_email_reply_choice(self, question_id: str, choices: list[str]) -> str:
        """Handle HUD reply options for drafts created from the selected email."""
        draft_entry = self._pending_email_reply_drafts.get(question_id)
        if not draft_entry:
            return "I couldn't find that reply draft, Sir."
        choice = next((ch.upper() for ch in choices if isinstance(ch, str) and ch.strip()), None)
        if not choice:
            return "I didn't catch which option you wanted, Sir."
        logger.info("[EmailHUD] Reply choice %s for question_id=%s", choice, question_id)
        if choice == "A":
            payload = self.pending_choices.get(question_id)
            if not payload:
                return "Those reply options expired, Sir."
            response = await self._process_email_reply_send(question_id, payload)
            self._pending_email_reply_drafts.pop(question_id, None)
            return response
        if choice == "B":
            self.email_edit_context = {
                "question_id": question_id,
                "email": draft_entry.get("email"),
                "topic": "email.reply",
            }
            return "Tell me how you'd like to adjust the draft, Sir."
        if choice == "C":
            self._pending_email_reply_drafts.pop(question_id, None)
            self.pending_choices.pop(question_id, None)
            await self._send_email_context_status(question_id, "Draft discarded.")
            return "Draft discarded, Sir."
        return "I didn't recognise that option, Sir."

    async def _handle_email_reply_followup(self, payload: dict, choices: list[str]):
        question_id = payload.get("question_id")
        email_meta = payload.get("email") or {}
        choice = next((ch for ch in choices if ch in ("A", "B", "C")), None)
        if not choice:
            return "I didn't catch which option you wanted, Sir."
        logger.info("[EmailHUD] Followup choice received: %s", choice)
        if choice == "A":
            return await self._process_email_reply_send(question_id, payload)
        if choice == "B":
            self.email_edit_context = {
                "question_id": question_id,
                "email": email_meta,
                "topic": payload.get("topic"),
            }
            return "What would you like me to change about the draft, Sir?"
        await self._send_email_context_status(question_id, "Draft discarded.")
        self.pending_choices.pop(question_id, None)
        return "Understood, Sir. The draft is discarded."

    async def _process_email_reply_send(self, question_id: str, payload: dict):
        email_meta = payload.get("email") or {}
        draft = payload.get("draft") or ""
        if not draft:
            draft = await self._generate_email_draft(email_meta, None)
            self.pending_choices[question_id]["draft"] = draft
        to_addr = email_meta.get("from") or ""
        thread_id = email_meta.get("threadId")
        subject = email_meta.get("subject") or "your email"
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
        try:
            result = await asyncio.to_thread(send_reply, thread_id, to_addr, subject, draft)
        except Exception as exc:
            return f"I couldn't send the reply: {exc}"
        if not isinstance(result, dict) or not result.get("success"):
            reason = result.get("reason") if isinstance(result, dict) else "unknown error"
            return f"I couldn't send the reply: {reason}"
        status = f"Reply sent successfully to {to_addr or 'the sender'}."
        await self._send_email_context_status(question_id, status)
        self.pending_choices.pop(question_id, None)
        return status

    async def _route_agent_intent(
        self,
        intent: Dict[str, Any],
        raw_text: str | None = None,
        query_id: str | None = None,
        return_response: bool = False,
    ) -> str | Dict[str, Any] | None:
        if not intent:
            return None
        domain = intent.get("domain")
        if not domain:
            return None
        agent = getattr(self, "agent_registry", {}).get(domain)
        if not agent:
            return None

        context = {"original_text": raw_text or ""}
        try:
            response = await agent.execute(intent, context=context)
        except Exception as exc:  # noqa: BLE001
            logger.error("[AgentRoute] %s agent failed: %s", domain, exc)
            fallback = {
                "status": "error",
                "speech": "I couldn't complete that request right now, Sir.",
                "error": str(exc),
            }
            if return_response:
                return fallback
            return fallback["speech"]

        if return_response:
            return response

        speech = response.get("speech") or response.get("message")
        if not speech:
            speech = "I've handled your request, Sir."

        if domain == WebSearchAgent.DOMAIN:
            if hasattr(self, "hud_event_sink") and callable(self.hud_event_sink):
                try:
                    await self._handle_web_search_hud(intent, response, query_id=query_id)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("[AgentRoute] Web HUD emit failed: %s", exc)
            return speech

        hud_payload = response.get("hud")
        if hud_payload and hasattr(self, "hud_event_sink") and callable(self.hud_event_sink):
            reply_options = response.get("reply_options")
            try:
                await self._send_hud_panel(
                    hud_payload,
                    query_id=query_id,
                    reply_options=reply_options,
                    reset_hud=True,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("[AgentRoute] HUD emit failed: %s", exc)

        return speech

    async def _handle_email_summary(self):
        try:
            result = await asyncio.to_thread(fetch_unread_summary, self.openai_client, 20)
        except FileNotFoundError:
            return "Email access is not configured (missing Gmail token)."
        except Exception as exc:
            logger.error("Email summary failed: %s", exc)
            return f"Email summary failed: {exc}"

        messages = result.get("messages", []) if isinstance(result, dict) else []
        # Classification pass per message
        classified = []
        for msg in messages:
            classification = classify_email(self.openai_client, msg)
            logger.info(
                "[EmailClassify] message_id=%s categories=%s importance=%.2f flags=%s",
                msg.get("id") or msg.get("snippet", "")[:20],
                classification.get("categories"),
                classification.get("importance_score"),
                {k: v for k, v in classification.items() if k not in ("categories", "importance_score")},
            )
            msg["classification"] = classification
            classified.append(msg)
        messages = classified
        suspicious_count = len([m for m in messages if m.get("is_suspicious")])
        total = len(messages)
        # Incremental awareness using today's library entry
        london_tz = ZoneInfo("Europe/London")
        today_key = datetime.now(london_tz).date().isoformat()
        existing_entry = get_latest_library_item("email_summary", date_key=today_key)
        covered_ids = set(existing_entry.get("metadata", {}).get("covered_message_ids", [])) if existing_entry else set()
        new_messages = [m for m in messages if m.get("id") and m.get("id") not in covered_ids]
        new_count = len(new_messages)
        top_subjects = ", ".join(m.get("subject", "(no subject)") for m in new_messages[:3] or messages[:3])
        summary_text = (
            f"Since your last summary, {new_count} new unread emails. Today we considered {total} total. "
            f"Top subjects: {top_subjects}" if total else "No unread emails right now."
        )
        logger.info(
            "[EmailSummary] Today=%s new_count=%d total_unread=%d suspicious=%d",
            today_key,
            new_count,
            total,
            suspicious_count,
        )
        spoken_len = len(summary_text)
        if spoken_len > SPOKEN_LENGTH_WATERMARK:
            logger.warning("Spoken response length high (email): %d chars", spoken_len)
        else:
            logger.info("Spoken response length (email): %d chars", spoken_len)

        vault_path = write_email_summary(self.file_service, messages)
        memory_id = None
        if self.memory:
            memory_id = self.memory.add_conversation_memory(
                text=f"Email summary: {summary_text}",
                metadata={"category": "email", "source": "email_service", "timestamp": datetime.now().isoformat()},
            )
        messages_to_write = new_messages if new_messages else messages
        # Save to library index daily
        now = datetime.now(london_tz)
        date_key = today_key
        library_path = None
        try:
            library_path = write_daily_email_summary_section(
                file_service=self.file_service,
                date_key=date_key,
                messages=messages_to_write,
                summary_text=summary_text,
                now=now,
            )
            all_ids = list({*(m.get("id") for m in messages if m.get("id")), *covered_ids})
            upsert_library_item(
                category="email_summary",
                title=f"Daily Email Summary – {date_key}",
                tags=["email", "summary", "daily"],
                library_path=library_path,
                metadata={
                    "covered_message_ids": all_ids,
                    "unread_count": total,
                    "suspicious_count": suspicious_count,
                    "from_time": existing_entry.get("metadata", {}).get("from_time") if existing_entry else None,
                    "to_time": now.isoformat(),
                    "summary_type": "incremental",
                    "new_count": new_count,
                },
                date_key=date_key,
            )
        except Exception as exc:
            logger.warning("[JarvisLibrary] Failed to save daily email summary: %s", exc)

        return {
            "spoken_text": summary_text,
            "extra": {"total": total, "suspicious": suspicious_count},
            "vault_path": vault_path,
            "memory_id": memory_id,
            "library_path": library_path,
        }

    async def _handle_email_read(self, text: str, query_id: str | None = None):
        parsed = self._parse_email_read_request(text)
        sender = parsed.get("sender")
        topic = parsed.get("topic")
        logger.info("[EmailRead] Detected read-email intent: \"%s\" sender=%s topic=%s", text, sender, topic)
        # Stage 1: deterministic inbox scan with identity resolution
        chosen = None
        canonical = None
        sender_tokens = []
        if sender:
            canonical, sender_tokens = identity_resolver.resolve_input_identity(sender)
            if not sender_tokens:
                sender_tokens = [identity_resolver.normalize_token(t) for t in sender.split() if identity_resolver.normalize_token(t)]
            try:
                inbox_msgs = await asyncio.to_thread(list_inbox_messages, 100)
            except FileNotFoundError:
                return "Email access is not configured (missing Gmail token)."
            except Exception as exc:
                logger.error("[EmailRead] Inbox list failed: %s", exc)
                inbox_msgs = []
            for msg in inbox_msgs:
                from_field = (msg.get("from") or "").lower()
                fields = {"from": from_field}
                matched_identity = identity_resolver.match_sender_fields(fields)
                tokens_match = all(tok in identity_resolver.normalize_token(from_field) for tok in sender_tokens)
                alias_hit = canonical and matched_identity == canonical
                if tokens_match or alias_hit:
                    chosen = msg
                    if not canonical and matched_identity:
                        canonical = matched_identity
                    logger.info(
                        "[EmailRead] Last-from scan tokens=%s matched id=%s subject=\"%s\"",
                        sender_tokens,
                        msg.get("id"),
                        msg.get("subject"),
                    )
                    break

        # Stage 2: query-based if no match and sender provided
        if not chosen and sender:
            query = f"from:({sender})"
            try:
                svc = google_helper.build_service("gmail")
                resp = (
                    svc.users()
                    .messages()
                    .list(userId="me", q=query, maxResults=50)
                    .execute()
                )
                ids = resp.get("messages", [])
                candidates: list[dict] = []
                for msg in ids:
                    detail = (
                        svc.users()
                        .messages()
                        .get(
                            userId="me",
                            id=msg["id"],
                            format="metadata",
                            metadataHeaders=["From", "Subject", "Date"],
                        )
                        .execute()
                    )
                    headers = detail.get("payload", {}).get("headers", [])
                    header_map = {h["name"]: h["value"] for h in headers}
                    candidates.append(
                        {
                            "id": msg["id"],
                            "threadId": detail.get("threadId"),
                            "from": header_map.get("From", ""),
                            "subject": header_map.get("Subject", ""),
                            "snippet": detail.get("snippet", ""),
                            "internalDate": detail.get("internalDate"),
                        }
                    )
                logger.info("[EmailRead] Query=%s count=%d", query, len(candidates))
                if candidates:
                    chosen = candidates[0]
            except FileNotFoundError:
                return "Email access is not configured (missing Gmail token)."
            except Exception as exc:
                logger.error("[EmailRead] Stage 2 query failed: %s", exc)

        # Stage 3: no sender provided, take latest inbox
        if not chosen and not sender:
            try:
                inbox_msgs = await asyncio.to_thread(list_inbox_messages, 50)
                if inbox_msgs:
                    chosen = inbox_msgs[0]
                    logger.info("[EmailRead] No sender provided; using latest inbox id=%s", chosen.get("id"))
            except Exception as exc:
                logger.error("[EmailRead] Latest inbox fetch failed: %s", exc)

        if not chosen:
            logger.info("[EmailRead] No messages found for sender=%s", sender)
            return "I could not find an email that matches that description, Sir."

        logger.info("[EmailRead] Chosen message_id=%s subject=%s", chosen.get("id"), chosen.get("subject"))
        try:
            fetched = await asyncio.to_thread(fetch_full_message, chosen.get("id"))
            if isinstance(fetched, tuple) and len(fetched) >= 2:
                meta, body = fetched[0], fetched[1]
            elif isinstance(fetched, dict):
                meta, body = fetched, fetched.get("body", "")
            else:
                raise ValueError(f"Unexpected email payload type: {type(fetched)}")
        except Exception as exc:
            return f"I couldn't open that email: {exc}"

        self.current_email = {
            "id": meta.get("id"),
            "threadId": meta.get("threadId"),
            "from": meta.get("from"),
            "subject": meta.get("subject"),
            "date": meta.get("date"),
            "body": body,
            "snippet": meta.get("snippet") or (body or "")[:240],
        }
        self.current_email_identity = canonical
        logger.info(
            "[EmailFocus] set to id=%s subject=\"%s\" from=\"%s\"",
            meta.get("id"),
            meta.get("subject"),
            meta.get("from"),
        )
        self._last_email_focus = dict(self.current_email)

        # Decide hybrid mode based on body length
        body_len = len(body or "")
        summary_only = body_len > 800
        summary_text = ""
        if summary_only:
            prompt = (
                "Summarise this email in 2-4 sentences for voice. "
                "Skip unsubscribe links and boilerplate. Focus on key details."
            )
            try:
                completion = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model=self.ai_model,
                    messages=[
                        {"role": "system", "content": prompt},
                        {
                            "role": "user",
                            "content": f"From: {meta.get('from')}\nSubject: {meta.get('subject')}\n\n{body}",
                        },
                    ],
                    max_tokens=MAX_CHAT_TOKENS,
                )
                summary_text = completion.choices[0].message.content or ""
            except Exception as exc:
                logger.warning("[EmailRead] Summarisation failed: %s", exc)
                summary_text = ""
        else:
            summary_text = body

        spoken_text = ""
        mode = "hybrid"
        if summary_only and summary_text:
            spoken_text = f"This email from {meta.get('from')} is about: {summary_text} Would you like the full text as well, Sir?"
            mode = "summary_only"
        else:
            spoken_text = (
                f"From {meta.get('from')}, subject {meta.get('subject')}. {summary_text[:600]}".strip()
            )
            mode = "full" if not summary_only else "hybrid"

        logger.info(
            "[EmailRead] Reading message_id=%s subject=%s mode=%s",
            meta.get("id"),
            meta.get("subject"),
            mode,
        )

        # Update library index metadata (non-writing path)
        try:
            add_library_item(
                category="email",
                title=f"Read email: {meta.get('subject')}",
                tags=["read"],
                library_path="operation:read_email",
                metadata={
                    "message_id": meta.get("id"),
                    "thread_id": meta.get("threadId"),
                    "read_to_user": True,
                    "last_read_time": datetime.now().isoformat(),
                },
            )
        except Exception as exc:
            logger.warning("[EmailRead] Failed to record read metadata: %s", exc)

        await self._send_email_focus_panel(query_id, self.current_email)
        await self._send_email_context_summary(query_id, summary_text or "Summary unavailable.")
        email_topic = f"Email: {self._preview_text(meta.get('subject', ''), 60)}"
        await self._send_email_reply_options(query_id, self.current_email, email_topic)
        return {
            "spoken_text": spoken_text,
            "extra": {"mode": mode, "message_id": meta.get("id")},
        }

    async def _handle_email_reply_request(self, text: str):
        if not self._last_email_focus:
            return "I don’t have a recent email in focus to reply to, Sir. Ask me to read or select an email first."

        email_meta = self._last_email_focus
        logger.info("[EmailReply] Drafting reply for message_id=%s", email_meta.get("id"))
        draft = await self._generate_email_draft(email_meta, text)
        if not draft:
            logger.warning("[EmailReply] Draft generation returned empty for message_id=%s", email_meta.get("id"))
            return "I couldn't draft a reply right now, Sir."

        question_id = await self._send_email_reply_options(None, email_meta, "email.reply", draft=draft)
        self._pending_email_reply_drafts[question_id] = {
            "draft": draft,
            "email": dict(email_meta),
        }
        await self._send_email_context_draft(question_id, draft)
        logger.info("[EmailReply] Drafted reply for message_id=%s question_id=%s", email_meta.get("id"), question_id)
        return {
            "spoken_text": "I’ve drafted a reply to this email, Sir. Choose A to send, B to edit, or C to discard.",
            "extra": {"message_id": email_meta.get("id")},
        }

    async def _handle_reply_confirmation(self, confirm: bool):
        pending = self.pending_reply
        self.pending_reply = None
        if not pending:
            return "There is no pending reply to send, Sir."

        if not confirm:
            logger.info("[EmailReply] User declined to send reply.")
            return "Understood, Sir. I won’t send it."

        target = pending.get("target") or {}
        draft = pending.get("draft") or ""
        thread_id = target.get("threadId")
        to_addr = target.get("from") or ""
        subject = f"Re: {target.get('subject')}"

        try:
            sent_id = await asyncio.to_thread(send_reply, thread_id, to_addr, subject, draft)
        except Exception as exc:
            return f"I couldn't send the reply: {exc}"

        try:
            add_library_item(
                category="email",
                title=f"Reply sent: {subject}",
                tags=["reply"],
                library_path="operation:reply_sent",
                metadata={
                    "reply_message_id": sent_id,
                    "thread_id": thread_id,
                    "original_message_id": target.get("id"),
                    "timestamp": datetime.now().isoformat(),
                },
            )
        except Exception as exc:
            logger.warning("[EmailReply] Failed to record reply metadata: %s", exc)

        logger.info("[EmailReply] Sent reply for message_id=%s with reply_id=%s", target.get("id"), sent_id)
        return "Done, Sir. I’ve sent your reply."

    async def _handle_email_summary_recall(self, text: str):
        date_key = self._resolve_summary_date(text)
        logger.info("[EmailSummaryRecall] Resolved date_key=%s from text=\"%s\"", date_key, text)
        entry = get_latest_library_item("email_summary", date_key=date_key)
        if not entry:
            logger.info("[EmailSummaryRecall] No summary found for date_key=%s", date_key)
            return f"I don’t have a saved email summary for {date_key}, Sir."

        path = entry.get("library_path")
        if not path or not Path(path).exists():
            logger.warning("[EmailSummaryRecall] Entry missing file at %s", path)
            return f"I could not load the saved summary file for {date_key}, Sir."

        content = Path(path).read_text(encoding="utf-8")
        try:
            completion = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": "Summarise this email log in 2-3 sentences for voice. Do not invent new content."},
                    {"role": "user", "content": content},
                ],
                max_tokens=MAX_CHAT_TOKENS,
            )
            recap = completion.choices[0].message.content or ""
        except Exception as exc:
            logger.warning("[EmailSummaryRecall] LLM recap failed: %s", exc)
            recap = content[:400]

        logger.info("[EmailSummaryRecall] Served summary for date_key=%s path=%s", date_key, path)
        return {
            "spoken_text": f"Email summary for {date_key}: {recap}",
            "extra": {"date_key": date_key, "library_path": path},
        }

    async def _handle_mark_read_request(self, text: str):
        try:
            window = self._resolve_mark_read_window(text)
            from_time = window["from"]
            to_time = window["to"]
            logger.info(
                "[EmailMarkRead] Resolved time window: from=%s to=%s source=%s",
                from_time.isoformat(),
                to_time.isoformat(),
                window.get("source"),
            )
            try:
                messages = await asyncio.to_thread(search_messages_in_window, from_time, to_time)
            except FileNotFoundError:
                return "Email access is not configured (missing Gmail token)."
            except Exception as exc:
                logger.error("[EmailMarkRead] Search failed: %s", exc)
                return f"Email mark-read search failed: {exc}"

            if not messages:
                logger.info("[EmailMarkRead] No messages found in window.")
                return "Sir, there are no emails in that time range to mark as read."

            count = len(messages)
            self.pending_mark_read = {
                "messages": messages,
                "window": window,
            }
            warn = ""
            if count > 100:
                warn = " That is quite a lot; please confirm."
            prompt = (
                f"I found {count} unread emails since {from_time.strftime('%H:%M')}. "
                f"Mark them all as read?{warn}"
            )
            logger.info("[EmailMarkRead] Gmail search returned %d candidates; awaiting confirmation.", count)
            return {
                "spoken_text": prompt,
                "extra": {"count": count, "window": {"from": from_time.isoformat(), "to": to_time.isoformat()}},
            }
        except Exception as exc:
            logger.error("[EmailMarkRead] Handler error: %s", exc)
            return f"Email mark-read handler failed: {exc}"

    def _record_mark_read_operation(self, window: dict, requested: int, updated: int):
        metadata = {
            "operation": "bulk_mark_read",
            "from": window.get("from").isoformat() if window.get("from") else None,
            "to": window.get("to").isoformat() if window.get("to") else None,
            "requested": requested,
            "updated": updated,
        }
        try:
            add_library_item(
                category="operation",
                title="Bulk mark-as-read",
                tags=["mark_read"],
                library_path="operation:mark_read",
                metadata=metadata,
            )
        except Exception as exc:
            logger.warning("[EmailMarkRead] Failed to record mark-read operation: %s", exc)

    async def _handle_mark_read_confirmation(self, confirm: bool):
        pending = self.pending_mark_read or {}
        self.pending_mark_read = None
        messages = pending.get("messages") or []
        window = pending.get("window") or {}
        if not messages:
            return "There is no pending mark-as-read request, Sir."

        if not confirm:
            logger.info("[EmailMarkRead] User declined mark-as-read request.")
            return "Understood. I will not mark any emails as read."

        ids = [m.get("id") for m in messages if m.get("id")]
        try:
            updated = await asyncio.to_thread(mark_messages_read, ids)
        except FileNotFoundError:
            return "Email access is not configured (missing Gmail token)."
        except Exception as exc:
            logger.error("[EmailMarkRead] Failed to mark messages read: %s", exc)
            return f"I could not mark the emails as read: {exc}"

        self._record_mark_read_operation(window, len(ids), updated)
        start_dt = window.get("from")
        start_str = start_dt.strftime("%H:%M") if hasattr(start_dt, "strftime") else "the requested window"
        logger.info(
            "[EmailMarkRead] Marked %d emails as read (requested %d) from=%s to=%s",
            updated,
            len(ids),
            window.get("from"),
            window.get("to"),
        )
        return f"Done, Sir. Marked {updated} emails as read from {start_str}."

    async def _handle_calendar(self, mode: str):
        try:
            if mode == "today":
                events = await asyncio.to_thread(get_today_agenda)
                label = "Today"
            elif mode == "tomorrow":
                events = await asyncio.to_thread(get_tomorrow_agenda)
                label = "Tomorrow"
            else:
                ev = await asyncio.to_thread(get_next_important_event)
                events = [ev] if ev else []
                label = "Next Important Event"
        except FileNotFoundError:
            return "Calendar access is not configured (missing calendar token)."
        except Exception as exc:
            logger.error("Calendar fetch failed: %s", exc)
            return f"Calendar fetch failed: {exc}"

        if mode == "next":
            if not events:
                summary_text = "No upcoming important events found."
            else:
                ev = events[0]
                summary_text = f"Next event: {ev.get('title')} at {ev.get('start')}."
        else:
            if not events:
                summary_text = f"{label}: no events."
            else:
                titles = ", ".join(ev.get("title", "(no title)") for ev in events[:3])
                summary_text = f"{label} has {len(events)} events. Top: {titles}."
        logger.info("Calendar handler returned %d events for %s", len(events), mode)
        spoken_len = len(summary_text)
        if spoken_len > SPOKEN_LENGTH_WATERMARK:
            logger.warning("Spoken response length high (calendar): %d chars", spoken_len)
        else:
            logger.info("Spoken response length (calendar): %d chars", spoken_len)

        vault_path = write_calendar_briefing(self.file_service, label, events)
        memory_id = None
        if self.memory:
            memory_id = self.memory.add_conversation_memory(
                text=f"Calendar {label.lower()} summary: {summary_text}",
                metadata={"category": "calendar", "source": "calendar_service", "timestamp": datetime.now().isoformat()},
            )

        # Library calendar stub
        try:
            cal_dir = Path("/mnt/f/JARVIS_LIBRARY/docs/calendar")
            cal_dir.mkdir(parents=True, exist_ok=True)
            date_key = datetime.now().date().isoformat()
            file_path = cal_dir / f"{date_key}_calendar_{label.lower().replace(' ', '_')}.md"
            lines = [
                f"# Calendar Summary – {label}",
                "",
                f"Generated: {datetime.now().isoformat()}",
                "",
                f"Events count: {len(events)}",
                "",
                "## Events",
            ]
            for ev in events:
                lines.append(f"- {ev.get('title', '(no title)')} at {ev.get('start')}")
            file_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
            upsert_library_item(
                category="calendar_summary",
                title=f"Calendar Summary – {label}",
                tags=["calendar", "summary"],
                library_path=str(file_path),
                metadata={"event_count": len(events), "label": label},
                date_key=date_key,
            )
            logger.info("[CalendarSummary] Saved calendar summary to %s", file_path)
        except Exception as exc:
            logger.warning("[CalendarSummary] Failed to save calendar summary: %s", exc)

        return {
            "spoken_text": summary_text,
            "extra": {"count": len(events), "label": label},
            "vault_path": vault_path,
            "memory_id": memory_id,
        }

    def _list_upcoming_events(self, days_ahead: int = 30) -> list[dict]:
        """List upcoming events within days_ahead window."""
        try:
            service = google_helper.build_service("calendar")
        except Exception as exc:
            logger.error("[CalendarList] Failed to init calendar service: %s", exc)
            return []
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days_ahead)
        try:
            resp = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now.isoformat(),
                    timeMax=end.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = resp.get("items", [])
            logger.info("[CalendarList] Retrieved %d upcoming events", len(events))
            return events
        except Exception as exc:
            logger.error("[CalendarList] Failed to list events: %s", exc)
            return []

    def _match_calendar_event(self, text: str, events: list[dict]) -> Optional[dict]:
        """Fuzzy match an event based on date phrase and summary tokens."""
        lower = (text or "").lower()
        date_pref = None
        london_tz = ZoneInfo("Europe/London")
        now = datetime.now(london_tz).date()
        if "today" in lower:
            date_pref = now
        elif "tomorrow" in lower:
            date_pref = now + timedelta(days=1)
        else:
            weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for idx, name in enumerate(weekdays):
                if name in lower:
                    days_ahead = (idx - now.weekday()) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    date_pref = now + timedelta(days=days_ahead)
                    break
        tokens = [t for t in re.findall(r"[a-zA-Z]+", text.lower()) if len(t) > 2]
        best = None
        best_score = 0
        for ev in events:
            start = ev.get("start", {}) or {}
            start_date = start.get("date")
            start_dt = start.get("dateTime")
            ev_date = None
            if start_date:
                ev_date = datetime.fromisoformat(start_date).date()
            elif start_dt:
                try:
                    ev_date = datetime.fromisoformat(start_dt.replace("Z", "+00:00")).astimezone(london_tz).date()
                except Exception:
                    ev_date = None
            if date_pref and ev_date and ev_date != date_pref:
                continue
            summary = (ev.get("summary") or "").lower()
            score = sum(1 for t in tokens if t in summary)
            if score > best_score:
                best_score = score
                best = ev
        if best_score == 0:
            return None
        return best

    async def _handle_calendar_add(self, text: str):
        try:
            event_spec = self._parse_calendar_add_spec(text)
            logger.info("[CalendarParse] add_event spec=%s", event_spec)
            result = await asyncio.to_thread(calendar_create_event, event_spec)
            if isinstance(result, dict) and result.get("success"):
                start = result.get("start", {})
                date_part = start.get("date") or start.get("dateTime") or ""
                return f"I've added '{result.get('summary')}' on {date_part}, Sir."
            err = result.get("error") if isinstance(result, dict) else "unknown error"
            return f"I couldn't add that event because Google returned: {err}"
        except Exception as exc:
            logger.error("[CalendarAction] add_event failed: %s", exc)
            return f"I couldn't add that event: {exc}"

    async def _handle_calendar_update(self, text: str):
        events = self._list_upcoming_events()
        target = self._match_calendar_event(text, events)
        if not target:
            return "I couldn't confidently identify which event to change, Sir."
        start = target.get("start", {}) or {}
        london_tz = ZoneInfo("Europe/London")
        now = datetime.now(london_tz)
        # Parse new time/date
        new_spec = self._parse_calendar_add_spec(text)
        patch = {}
        if new_spec.get("all_day"):
            patch["start"] = {"date": new_spec["start"].date().isoformat()}
            patch["end"] = {"date": new_spec["end"].date().isoformat()}
        else:
            patch["start"] = {"dateTime": new_spec["start"].isoformat(), "timeZone": new_spec.get("timezone", "Europe/London")}
            patch["end"] = {"dateTime": new_spec["end"].isoformat(), "timeZone": new_spec.get("timezone", "Europe/London")}
        logger.info("[CalendarParse] update target=%s patch=%s", target.get("id"), patch)
        try:
            result = await asyncio.to_thread(calendar_update_event, target.get("id"), patch)
            if result.get("success"):
                start_info = result.get("details", {}).get("start", {}) if isinstance(result, dict) else {}
                date_part = start_info.get("date") or start_info.get("dateTime") or ""
                return f"I've updated '{result.get('details', {}).get('summary')}' to {date_part}, Sir."
            err = result.get("details", {}).get("error") if isinstance(result, dict) else "unknown error"
            return f"I couldn't update that event because Google returned: {err}"
        except Exception as exc:
            logger.error("[CalendarAction] update_event failed: %s", exc)
            return f"I couldn't update that event: {exc}"

    async def _handle_calendar_delete(self, text: str):
        events = self._list_upcoming_events()
        target = self._match_calendar_event(text, events)
        if not target:
            return "I couldn't confidently identify which event to cancel, Sir."
        question_id = self._generate_question_id()
        self.pending_choices[question_id] = {
            "question_id": question_id,
            "handler": "calendar_delete_event",
            "event": target,
        }
        topic = "Calendar delete confirmation"
        self._activate_followup(question_id, topic)
        summary = target.get("summary", "the event")
        start = target.get("start", {}) or {}
        when = start.get("date") or start.get("dateTime") or "the scheduled time"
        prompt = f"Do you want me to cancel '{summary}' on {when}, Sir? A: Yes, cancel it. B: Move it instead (not implemented). C: No, leave it."
        payload = {
            "type": "followup_choices",
            "question_id": question_id,
            "topic": topic,
            "choices": {"A": "Cancel it", "B": "Move it instead", "C": "Do nothing"},
        }
        try:
            if hasattr(self, "hud_event_sink") and callable(self.hud_event_sink):
                await self._emit_followup_choices(payload, "calendar")
                logger.info("[CalendarConfirm] Sent followup_choices question_id=%s", question_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[CalendarConfirm] Failed to send HUD event: %s", exc)
        return prompt
   
    def _maybe_force_web_search(self, text: str, intent: dict[str, Any] | None) -> dict[str, Any] | None:
        """Ensure general WH-questions without personal context invoke web search."""
        if not intent:
            return intent
        domain = intent.get("domain")
        skip_domains = {"email", "calendar", "docs", "reminder", "search", WebSearchAgent.DOMAIN}
        if domain in skip_domains:
            return intent
        normalized_text = (text or "").lower().strip()
        if not normalized_text:
            return intent
        sanitized = re.sub(r"[^a-z0-9 ]+", " ", normalized_text)
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        if not sanitized:
            return intent
        personal_patterns = (
            "my email",
            "my emails",
            "in my email",
            "my inbox",
            "my calendar",
            "my agenda",
            "my schedule",
            "my docs",
            "my documents",
            "my files",
            "that file",
            "this file",
            "my notes",
        )
        if any(pattern in sanitized for pattern in personal_patterns):
            return intent
        wh_prefixes = (
            "who ",
            "what ",
            "where ",
            "when ",
            "which ",
            "whom ",
            "whose ",
            "how many ",
            "how much ",
            "what s ",
            "whats ",
            "who s ",
            "whos ",
            "where s ",
            "wheres ",
        )
        if any(sanitized.startswith(prefix) for prefix in wh_prefixes):
            forced = dict(intent)
            forced["domain"] = WebSearchAgent.DOMAIN
            forced["action"] = "search"
            forced["search_term"] = forced.get("search_term") or text
            return forced
        return intent

    async def process_text_input(self, user_input):
        """
        Process text input and generate response
        This is the main intelligence function
        """
        try:
            self.stats['conversations'] += 1

            raw_text = user_input or ""

            if self.conversation_state.get("awaiting_followup"):
                logger.info(
                    "[DIALOG] User reply to question_id=%s: '%s'",
                    self.conversation_state.get("last_question_id") or "unknown",
                    self._preview_text(raw_text, 80),
                )
                last_qid = self.conversation_state.get("last_question_id")
                pending_payload = self.pending_choices.get(last_qid) if last_qid else None
                if pending_payload and pending_payload.get("handler") == "email_bulk_mark_read":
                    parsed_choices = self._parse_followup_option(raw_text)
                    if parsed_choices:
                        return await self.process_followup_choice(last_qid, parsed_choices)
                if pending_payload and pending_payload.get("handler") == "calendar_delete_event":
                    parsed_choices = self._parse_followup_option(raw_text)
                    if parsed_choices:
                        return await self.process_followup_choice(last_qid, parsed_choices)
                if pending_payload and pending_payload.get("handler") == "email_delete":
                    parsed_choices = self._parse_followup_option(raw_text)
                    if parsed_choices:
                        return await self.process_followup_choice(last_qid, parsed_choices)
                # If user simply says "more detail"/affirmation and we have structured choices, default to option A.
                if pending_payload and self._is_followup_affirmation(raw_text):
                    logger.info("[FOLLOWUP] Affirmation detected; routing to choice A for question_id=%s", last_qid)
                    return await self._process_followup_prompt(last_qid, ["A"])
                self.conversation_state["awaiting_followup"] = False

            sanitized_input, is_safe, warning = self.personality_engine.filter_dangerous_input(raw_text)
            working_input = sanitized_input if not is_safe else raw_text

            if not is_safe:
                print(f"ÔÜá´©Å Security warning: {warning}")
                working_input = sanitized_input

            handshake_result = self._run_conversation_handshake(working_input)
            working_input = handshake_result.get("final_text", working_input)
            if self.email_edit_context:
                return await self._handle_email_edit_instruction(working_input)
            query_id = self._generate_question_id()
            await self._reset_hud_for_new_query(query_id)

            logger.info("Intent routing: text='%s'", working_input)

            if self.pending_mark_read:
                if self._is_confirmation(working_input):
                    logger.info("[EmailMarkRead] Confirmation received for pending request.")
                    return await self._handle_mark_read_confirmation(True)
                if self._is_decline(working_input):
                    logger.info("[EmailMarkRead] Decline received for pending request.")
                    return await self._handle_mark_read_confirmation(False)

            if self.pending_reply:
                if self._is_confirmation(working_input):
                    logger.info("[EmailReply] Confirmation received for pending reply.")
                    return await self._handle_reply_confirmation(True)
                if self._is_decline(working_input):
                    logger.info("[EmailReply] Decline received for pending reply.")
                    return await self._handle_reply_confirmation(False)

            normalized_intent = None
            if self.meaning_normalizer:
                normalized_intent = self.meaning_normalizer.normalize(working_input)
                if (
                    AstraMeaningNormalizer.looks_like_web_query(working_input)
                    and normalized_intent.get("domain") not in {"web_search", ""}
                ):
                    normalized_intent["domain"] = WebSearchAgent.DOMAIN
                    normalized_intent["action"] = "search"
                    normalized_intent["search_term"] = normalized_intent.get("search_term") or working_input
                if normalized_intent.get("domain") == "clarify":
                    return normalized_intent.get("question") or "Could you clarify your request, Sir?"

            routed_intent = self._maybe_force_web_search(working_input, normalized_intent)
            if routed_intent is not normalized_intent and routed_intent and routed_intent.get("domain") == WebSearchAgent.DOMAIN:
                logger.info(
                    "[Router] Escalated general WH-question to web_search: search_term=%r",
                    routed_intent.get("search_term"),
                )

            if routed_intent and routed_intent.get("domain") == "email" and routed_intent.get("action") in {"search", "search_emails_by_query"}:
                logger.info("[EmailSearch] Routing to email search handler via normalizer: %s", working_input)
                return await self._handle_email_search(
                    working_input,
                    query=routed_intent.get("search_term") or working_input,
                    fuzzy_allowed=bool(routed_intent.get("fuzzy_allowed")),
                )
            if (
                routed_intent
                and routed_intent.get("domain") in {WebSearchAgent.DOMAIN, "search"}
                and routed_intent.get("action") in {"search", "web_search"}
            ):
                web_query = routed_intent.get("search_term") or working_input
                logger.info("[WebSearch] Routing to web search handler via normalizer: %s", web_query)
                return await self._handle_web_search(web_query, query_id=query_id)
            if routed_intent:
                agent_response = await self._route_agent_intent(routed_intent, working_input, query_id=query_id)
                if agent_response:
                    return agent_response

            search_query = self._extract_search_query(working_input)
            if search_query:
                logger.info("Routing to web search handler.")
                return await self._handle_web_search(search_query, query_id=query_id)

            if self._is_mark_read_intent(working_input):
                logger.info(f"[EmailMarkRead] Detected mark-as-read intent: \"{working_input}\"")
                return await self._handle_mark_read_request(working_input)

            if self._is_email_read_intent(working_input):
                logger.info(f"[EmailRead] Routing to read-email handler: {working_input}")
                return await self._handle_email_read(working_input, query_id=query_id)

            if self._is_email_bulk_risky(working_input):
                logger.info("[EmailBulkRisk] Detected risky bulk email intent: %s", working_input)
                return await self._handle_email_bulk_risky(working_input)

            if self._is_email_intent(working_input):
                logger.info(f"Routing to EMAIL handler: {working_input}")
                return await self._handle_email_summary()

            cal_action_intent = self._detect_calendar_intent(working_input)
            if cal_action_intent == "calendar_add_event":
                logger.info("[CalendarIntent] add_event: %s", working_input)
                return await self._handle_calendar_add(working_input)
            if cal_action_intent == "calendar_update_event":
                logger.info("[CalendarIntent] update_event: %s", working_input)
                return await self._handle_calendar_update(working_input)
            if cal_action_intent == "calendar_delete_event":
                logger.info("[CalendarIntent] delete_event: %s", working_input)
                return await self._handle_calendar_delete(working_input)

            if self._is_reply_intent(working_input):
                logger.info(f"[EmailReply] Routing to reply handler: {working_input}")
                return await self._handle_email_reply_request(working_input)

            if self._is_email_summary_recall_intent(working_input):
                logger.info(f"[EmailSummaryRecall] Detected recall intent: {working_input}")
                return await self._handle_email_summary_recall(working_input)

            cal_intent = self._calendar_intent(working_input)
            if cal_intent:
                logger.info(f"Routing to CALENDAR handler: {working_input} (mode={cal_intent})")
                return await self._handle_calendar(cal_intent)

            if self._is_time_query(working_input):
                time_response, current_time = self._get_current_time_response()
                return time_response

            context_xml = self.context_manager.build_context(working_input)

            london_tz = ZoneInfo("Europe/London")
            now = datetime.now(london_tz)
            now_iso = now.isoformat()
            now_human = now.strftime("%A %d %B %Y, %H:%M, %Z")

            print(f"­ƒôà Injecting datetime into GPT context: {now_iso}")

            system_prompt = self._build_system_prompt()
            datetime_context = f"\n\nSYSTEM DATETIME: The current local datetime on the JARVIS PC Brain is {now_human} ({now_iso}). Use this as the source of truth for 'now', 'today', 'tomorrow', and all date/time calculations."
            system_prompt += datetime_context

            if len(working_input) >= LONG_QUERY_THRESHOLD:
                system_prompt += "\n\nLONG QUERY HANDLING: The user input is long; provide a 2-4 sentence overview, then ask 'Would you like a deeper dive into any part?' and stop."

            if context_xml:
                system_prompt += f"\n\n{context_xml}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": working_input},
            ]

            logger.info(
                "[DIALOG] Processing (preview): '%s' (len=%d)",
                self._preview_text(working_input, 80),
                len(working_input),
            )
            logger.info(
                "[LLM_INPUT] len=%d, preview='%s'",
                len(working_input),
                self._preview_text(working_input, 120),
            )
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.ai_model,
                messages=messages,
                max_tokens=MAX_CHAT_TOKENS,
            )

            ai_response = response.choices[0].message.content

            conversation_text = f"User: {working_input}\nJARVIS: {ai_response}"
            self.memory.add_conversation_memory(
                text=conversation_text,
                metadata={'type': 'conversation'}
            )

            suggestion = self.proactive_engine.analyze_and_suggest(
                user_input=working_input,
                conversation_history=None,
                current_time=None
            )

            if suggestion:
                ai_response += f"\n\n{suggestion}"

            if ai_response and len(ai_response) > 800:
                trimmed = ai_response[:800]
                trimmed = trimmed.rsplit(" ", 1)[0]
                ai_response = trimmed.strip() + " ... Would you like a deeper dive into any part, Sir?"

            spoken_len = len(ai_response or "")
            if spoken_len > SPOKEN_LENGTH_WATERMARK:
                logger.warning("Spoken response length high: %d chars", spoken_len)
            else:
                logger.info("Spoken response length: %d chars", spoken_len)

            if self._detect_followup_prompt(ai_response):
                prev_id = self.active_followup_question_id
                if prev_id:
                    await self._clear_reply_options(prev_id)
                question_id = self._generate_question_id()
                choices_payload = self._build_followup_choices(question_id, topic=self._preview_text(working_input, 60))
                self._activate_followup(question_id, choices_payload.get("topic"))
                logger.info(
                    "[DIALOG] Assistant asked a follow-up; awaiting user reply. question_id=%s",
                    question_id,
                )
                try:
                    # Emit HUD event for follow-up choices if server supports it
                    if hasattr(self, "hud_event_sink") and callable(self.hud_event_sink):
                        payload = {
                            "type": "followup_choices",
                            "question_id": question_id,
                            "topic": choices_payload.get("topic"),
                            "choices": choices_payload.get("choices"),
                        }
                        await self._emit_followup_choices(payload, "general")
                        logger.info("[FOLLOWUP] Sent followup_choices event for question_id=%s", question_id)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("[FOLLOWUP] Failed to send followup_choices event: %s", exc)
            else:
                self.conversation_state["awaiting_followup"] = False
                self.conversation_state["last_question_id"] = None

            return ai_response

        except Exception as e:
            print(f"ÔØî Processing error: {e}")
            return f"I encountered an error: {str(e)}"
    
    def _build_system_prompt(self):
        """Build the system prompt with personality and context"""
        # Get JARVIS personality from PersonalityEngine
        base_prompt = self.personality_engine.get_system_prompt()
        
        # Add system context
        system_context = f"""

SYSTEM INFORMATION:
Location: {self.location_name}
Platform: {self.system_info['platform']}
Runtime: Ubuntu WSL2 with GPU acceleration
Hostname: {self.system_info['hostname']}

RESPONSE RULES:
- Default to 2-4 sentences for normal answers; keep it concise and suited for TTS.
- For lists, use 3-5 bullet points max.
- End with a natural stop: "Let me know if you'd like more detail, Sir."
- If the user request is long/complex, give a short overview first (still concise) then ask: "Would you like a deeper dive into any part?"
- Keep the whole reply under ~800 characters; do not elaborate unless explicitly asked in a follow-up.
"""
        
        return base_prompt + system_context
    
    def generate_audio(self, text):
        """
        Generate audio from text using OpenAI TTS (fable voice)
        Note: Uses separate tts_client, not the Ollama client
        Returns audio data ready for playback
        """
        try:
            response = self.tts_client.audio.speech.create(
                model=self.voice_model,
                voice=self.voice_type,
                input=text
            )
            
            # Return audio bytes
            return response.content
            
        except Exception as e:
            print(f"ÔØî TTS error: {e}")
            return None
    
    def get_stats(self):
        """Get current statistics"""
        uptime = datetime.now() - self.stats['start_time']
        return {
            **self.stats,
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': str(uptime).split('.')[0]
        }
    
    async def test_brain(self):
        """Test the brain with a simple query"""
        print("\n­ƒº¬ Running brain test...\n")

        test_input = "Hello JARVIS, can you hear me?"
        response = await self.process_text_input(test_input)
        response_text = response.get("spoken_text") if isinstance(response, dict) else response

        print(f"­ƒôØ Response: {response_text}\n")

        stats = self.get_stats()
        print(f"­ƒôè Stats: {stats['conversations']} conversations, uptime: {stats['uptime_formatted']}\n")

        return True


async def main():
    """Main entry point for JARVIS Brain"""
    try:
        brain = JARVISBrain()

        await brain.test_brain()

        print("­ƒÆ¼ Interactive mode - Type 'exit' to quit\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['exit', 'quit', 'stop']:
                print("\n­ƒæï JARVIS Brain shutting down...")
                break

            if not user_input:
                continue

            response = await brain.process_text_input(user_input)
            response_text = response.get("spoken_text") if isinstance(response, dict) else response
            print(f"\nJARVIS: {response_text}\n")

    except KeyboardInterrupt:
        print("\n\n­ƒæï JARVIS Brain interrupted by user")
    except Exception as e:
        print(f"\nÔØî Fatal error: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n­ƒæï JARVIS Brain interrupted by user")
    except Exception as exc:
        print(f"\nÔØî Fatal error: {exc}")
        raise
