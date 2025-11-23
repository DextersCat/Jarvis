#!/usr/bin/env python3
"""
JARVIS Brain Module - Ubuntu WSL2 Version
PC Brain Migration - Phase C1

This is the core processing brain without audio I/O.
Designed to work with AI-Pi voice terminal via WebSocket.

Based on: Fresh Professional Astra AI with JARVIS Personality Framework
"""

import asyncio
import logging
import os
import platform
import psutil
import re
import socket
import sys
from datetime import datetime, timedelta
from pathlib import Path
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

# JARVIS personality modules
from personality_engine import PersonalityEngine
from context_manager import ContextManager
from proactive_engine import ProactiveSuggestionEngine
from jarvis_memory_system import JARVISMemory
from file_service import JarvisFileService
from services.search_service import search_web, summarise_search_results
from services.email_service import (
    fetch_unread_summary,
    write_email_summary,
    build_email_markdown,
    search_messages_in_window,
    mark_messages_read,
    search_messages_by_criteria,
    fetch_full_message,
    send_reply,
    write_daily_email_summary_section,
)
from services.calendar_service import (
    get_today_agenda,
    get_tomorrow_agenda,
    get_next_important_event,
    write_calendar_briefing,
)
from services.library_index import (
    add_item as add_library_item,
    get_latest as get_latest_library_item,
    upsert_item as upsert_library_item,
)
from services.email_classifier import classify_email

# Load environment variables
ENV_PATH = Path.home() / "JARVIS" / "config" / ".env"
load_dotenv(ENV_PATH)
load_dotenv()

logger = logging.getLogger(__name__)
LONG_QUERY_THRESHOLD = 350
SPOKEN_LENGTH_WATERMARK = 1200
MAX_CHAT_TOKENS = 200

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
        self.ai_model = "llama3"
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
        self.pending_mark_read = None
        self.current_email = None
        self.pending_reply = None

        # File service (stub, non-destructive)
        self.file_service = self._init_file_service()
        
        # System info
        self.system_info = self._get_system_info()
        
        # Initialize components
        self.init_brain_system()
    
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
                base_url='http://localhost:11434/v1',
                api_key='ollama'  # Local requires no real key
            )
            print("Ô£à Ollama llama3 initialized (F:\\JARVIS_MODELS)")
            
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
            print("   Ô£ô Proactive engine loaded")
            
            print("")
            print("=" * 60)
            print("Ô£à JARVIS BRAIN ONLINE - Ready for commands")
            print("=" * 60)
            print("")
            
        except Exception as e:
            print(f"ÔØî Initialization error: {e}")
            raise
    
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

    async def _handle_web_search(self, query: str):
        timestamp = datetime.now()
        results_payload = await search_web(query)
        results = results_payload.get("results", []) if isinstance(results_payload, dict) else []
        summary = await summarise_search_results(self.openai_client, query, results)

        vault_path = self._write_web_search_to_vault(query, summary, results, timestamp)
        memory_id = self._store_web_memory(query, summary, timestamp)

        links = [{"title": r.get("title", ""), "url": r.get("url", "")} for r in results[:3] if r.get("url")]
        spoken_len = len(summary or "")
        if spoken_len > SPOKEN_LENGTH_WATERMARK:
            logger.warning("Spoken response length high (web): %d chars", spoken_len)
        else:
            logger.info("Spoken response length (web): %d chars", spoken_len)
        payload = {
            "spoken_text": summary,
            "extra": {"links": links} if links else {},
        }
        if vault_path:
            payload["vault_path"] = vault_path
        if memory_id:
            payload["memory_id"] = memory_id

        return payload

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

    async def _handle_email_read(self, text: str):
        parsed = self._parse_email_read_request(text)
        sender = parsed.get("sender")
        topic = parsed.get("topic")
        logger.info("[EmailRead] Detected read-email intent: \"%s\" sender=%s topic=%s", text, sender, topic)
        try:
            candidates = await asyncio.to_thread(search_messages_by_criteria, sender, topic, max_items=5)
        except FileNotFoundError:
            return "Email access is not configured (missing Gmail token)."
        except Exception as exc:
            logger.error("[EmailRead] Search failed: %s", exc)
            return f"I could not search your email right now: {exc}"

        if not candidates:
            logger.info("[EmailRead] No messages found for query.")
            return "I could not find an email that matches that description, Sir."

        chosen = candidates[0]
        logger.info(
            "[EmailRead] Chosen message_id=%s subject=%s", chosen.get("id"), chosen.get("subject")
        )
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
        }

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

        return {
            "spoken_text": spoken_text,
            "extra": {"mode": mode, "message_id": meta.get("id")},
        }

    async def _handle_email_reply_request(self, text: str):
        if not self.current_email:
            return "I don’t have a recent email in focus to reply to, Sir. Ask me to read an email first."

        target = self.current_email
        logger.info("[EmailReply] Detected reply intent for message_id=%s", target.get("id"))
        instruction = text
        try:
            completion = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.ai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Draft a concise, polite reply in Jarvis butler style. "
                            "Keep it short and clear. Do not include quoted text."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Original email subject: {target.get('subject')}\n\nBody:\n{target.get('body')}\n\nUser instruction: {instruction}",
                    },
                ],
                max_tokens=MAX_CHAT_TOKENS,
            )
            draft = completion.choices[0].message.content or ""
        except Exception as exc:
            logger.error("[EmailReply] Draft failed: %s", exc)
            return f"I couldn't draft a reply: {exc}"

        self.pending_reply = {
            "target": target,
            "draft": draft,
        }
        logger.info("[EmailReply] Drafted reply for message_id=%s: %s", target.get("id"), draft)
        return {
            "spoken_text": f"Here is my proposed reply, Sir: {draft} Shall I send this reply?",
            "extra": {"message_id": target.get("id")},
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
    
    async def process_text_input(self, user_input):
        """
        Process text input and generate response
        This is the main intelligence function
        """
        try:
            self.stats['conversations'] += 1

            sanitized_input, is_safe, warning = self.personality_engine.filter_dangerous_input(user_input)
            working_input = sanitized_input if not is_safe else user_input
            logger.info(f"Intent routing: text='{working_input}'")

            if not is_safe:
                print(f"ÔÜá´©Å Security warning: {warning}")
                working_input = sanitized_input

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

            search_query = self._extract_search_query(working_input)
            if search_query:
                logger.info("Routing to web search handler.")
                return await self._handle_web_search(search_query)

            if self._is_mark_read_intent(working_input):
                logger.info(f"[EmailMarkRead] Detected mark-as-read intent: \"{working_input}\"")
                return await self._handle_mark_read_request(working_input)

            if self._is_email_read_intent(working_input):
                logger.info(f"[EmailRead] Routing to read-email handler: {working_input}")
                return await self._handle_email_read(working_input)

            if self._is_email_intent(working_input):
                logger.info(f"Routing to EMAIL handler: {working_input}")
                return await self._handle_email_summary()

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

            print(f"­ƒñö Processing: '{working_input}'")
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
