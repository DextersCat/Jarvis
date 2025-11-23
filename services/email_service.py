import asyncio
import base64
import json
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

TOKEN_DIR = Path.home() / ".jarvis_tokens"
GMAIL_TOKEN_FILE = TOKEN_DIR / "gmail_token.json"
CREDENTIALS_FILE = TOKEN_DIR / "credentials.json"
# Align scopes with issued token (read + modify); send scope omitted to avoid invalid_scope.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


def _load_gmail_service() -> object:
    logger.info("email_service module path: %s", __file__)
    logger.info("Gmail requested scopes: %s", SCOPES)
    if not GMAIL_TOKEN_FILE.exists():
        raise FileNotFoundError(f"Gmail token missing: {GMAIL_TOKEN_FILE}")
    creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_FILE), SCOPES)
    logger.info("Gmail token scopes (creds.scopes): %s", getattr(creds, "scopes", None))
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(f"Gmail credentials missing: {CREDENTIALS_FILE}")
            raise RuntimeError("Gmail credentials invalid; please re-authenticate.")
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _basic_suspicious_score(sender: str, subject: str, snippet: str) -> bool:
    sender_lower = sender.lower()
    subject_lower = subject.lower()
    snippet_lower = snippet.lower()
    bad_domains = ("@qq.", "@163.", "@proton.", "@tempmail", "no-reply@", "noreply@")
    bad_words = ("verify", "reset password", "urgent", "invoice", "payment", "suspended")
    if any(d in sender_lower for d in bad_domains):
        return True
    if any(w in subject_lower for w in bad_words):
        return True
    if "wire transfer" in snippet_lower or "bank" in snippet_lower:
        return True
    return False


async def _llm_mark_suspicious(llm_client, messages: List[Dict]) -> List[int]:
    if not llm_client or not messages:
        return []
    prompt_items = []
    for idx, msg in enumerate(messages[:10], start=1):
        prompt_items.append(
            f"{idx}. From: {msg.get('from')} | Subject: {msg.get('subject')} | Snippet: {msg.get('snippet')}"
        )
    user_content = (
        "Mark which emails look suspicious/phishing. "
        "Respond with comma-separated numbers only (e.g., 1,3). "
        "Be conservative.\n\nEmails:\n" + "\n".join(prompt_items)
    )
    try:
        completion = await asyncio.to_thread(
            llm_client.chat.completions.create,
            model="llama3",
            messages=[
                {"role": "system", "content": "You are a security filter."},
                {"role": "user", "content": user_content},
            ],
        )
        text = completion.choices[0].message.content or ""
        indices = []
        for part in text.replace(" ", "").split(","):
            if part.isdigit():
                indices.append(int(part))
        return indices
    except Exception as exc:
        logger.warning("LLM suspicious classification failed: %s", exc)
        return []


def _time_window(day_offset: int = 0, days_back: int = 0) -> Tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    if day_offset:
        now += timedelta(days=day_offset)
    start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc) - timedelta(days=days_back)
    end = start + timedelta(days=1)
    return start, end


def _build_query(after_ts: int, before_ts: Optional[int], sender: Optional[str], topic: Optional[str], unread_only: bool) -> str:
    parts = [f"after:{after_ts}"]
    if before_ts:
        parts.append(f"before:{before_ts}")
    if unread_only:
        parts.append("is:unread")
    if sender:
        parts.append(f"from:{sender}")
    if topic:
        parts.append(topic)
    return " ".join(parts)


def fetch_unread_summary(llm_client=None, max_items: int = 20) -> Dict:
    service = _load_gmail_service()
    messages = []
    try:
        logger.info(
            "Gmail API call: users().messages().list userId='me' maxResults=%s q='is:unread'",
            max_items,
        )
        resp = (
            service.users()
            .messages()
            .list(userId="me", q="is:unread", maxResults=max_items)
            .execute()
        )
        logger.info("Gmail API list response keys: %s", list(resp.keys()))
        ids = resp.get("messages", [])
        for msg in ids:
            detail = (
                service.users()
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
            sender = header_map.get("From", "(unknown)")
            subject = header_map.get("Subject", "(no subject)")
            snippet = detail.get("snippet", "")
            internal_date = detail.get("internalDate")
            received_at = (
                datetime.fromtimestamp(int(internal_date) / 1000, tz=timezone.utc).isoformat()
                if internal_date
                else None
            )
            messages.append(
                {
                    "from": sender,
                    "subject": subject,
                    "snippet": snippet,
                    "received_at": received_at,
                    "is_suspicious": False,
                    "id": msg.get("id"),
                    "threadId": detail.get("threadId"),
                }
            )
    except HttpError as exc:
        status = getattr(exc.resp, "status", None)
        logger.error("Failed to fetch Gmail messages (status=%s): %s", status, exc)
        content = getattr(exc, "content", b"")
        if content:
            try:
                logger.error("Gmail error content: %s", content.decode())
            except Exception:  # noqa: BLE001
                logger.error("Gmail error content (raw bytes): %s", content)
            try:
                logger.error("Gmail error parsed JSON: %s", json.loads(content))
            except Exception:
                pass
        raise

    for msg in messages:
        msg["is_suspicious"] = _basic_suspicious_score(
            msg["from"], msg["subject"], msg["snippet"]
        )

    suspicious_indices = asyncio.run(_llm_mark_suspicious(llm_client, messages))
    for idx in suspicious_indices:
        if 1 <= idx <= len(messages):
            messages[idx - 1]["is_suspicious"] = True

    return {"messages": messages}


def build_markdown(messages: List[Dict]) -> str:
    now = datetime.now(timezone.utc)
    lines = [
        "# Email Summary",
        "",
        f"**Timestamp:** {now.isoformat()}  ",
        "**Category:** email  ",
        "**Source:** email_service  ",
        "**Context:** Gmail unread summary",
        "",
        "## Overview",
        f"Unread messages: {len(messages)}",
        "",
        "## Suspicious candidates",
    ]
    suspicious = [m for m in messages if m.get("is_suspicious")]
    if suspicious:
        for msg in suspicious:
            lines.append(f"- {msg.get('subject')} — {msg.get('from')}")
    else:
        lines.append("- None flagged")
    lines.append("")
    lines.append("## Messages")
    for idx, msg in enumerate(messages, start=1):
        lines.append(f"{idx}. **{msg.get('subject')}** — {msg.get('from')}")
        lines.append(f"   Received: {msg.get('received_at')}")
        lines.append(f"   Snippet: {msg.get('snippet')}")
        if msg.get("is_suspicious"):
            lines.append("   ⚠️ Marked suspicious")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_email_markdown(messages: List[Dict]) -> str:
    return build_markdown(messages)


def write_email_summary(file_service, messages: List[Dict]) -> Optional[str]:
    if not file_service or not file_service.is_enabled:
        return None
    now = datetime.now()
    name = f"{now.strftime('%H%M')}_unread-summary"
    content = build_markdown(messages)
    result = file_service.create_file(
        name=name,
        ext="md",
        category="email",
        content=content,
        allow_overwrite=False,
    )
    if result.get("success"):
        return result.get("full_path")
    logger.warning("Failed to write email summary: %s", result.get("message"))
    return None


def write_daily_email_summary_section(
    file_service=None,
    messages: List[Dict] = None,
    date_key: Optional[str] = None,  # accepted but unused; keep behavior unchanged
    summary_text: Optional[str] = None,  # accepted but unused; keep behavior unchanged
    now: Optional[datetime] = None,  # accepted but unused; keep behavior unchanged
) -> Optional[str]:
    if not file_service or not getattr(file_service, "is_enabled", False):
        return None
    messages = messages or []
    now = now or datetime.now()
    name = f"{now.strftime('%Y%m%d')}_daily-email-summary"
    content = build_markdown(messages)
    result = file_service.create_file(
        name=name,
        ext="md",
        category="email",
        content=content,
        allow_overwrite=True,
    )
    if result.get("success"):
        return result.get("full_path")
    logger.warning("Failed to write daily email summary: %s", result.get("message"))
    return None


def search_messages_in_window(
    from_time: datetime,
    to_time: Optional[datetime] = None,
    unread_only: bool = True,
    max_items: int = 200,
) -> List[Dict]:
    service = _load_gmail_service()
    to_time = to_time or datetime.now(timezone.utc)
    query = _build_query(int(from_time.timestamp()), int(to_time.timestamp()), None, None, unread_only)
    messages: List[Dict] = []
    resp = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_items)
        .execute()
    )
    ids = resp.get("messages", [])
    logger.info("[EmailSearchWindow] Gmail search returned %d ids", len(ids))
    for msg in ids:
        detail = (
            service.users()
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
        messages.append(
            {
                "id": msg["id"],
                "threadId": detail.get("threadId"),
                "from": header_map.get("From", ""),
                "subject": header_map.get("Subject", ""),
                "snippet": detail.get("snippet", ""),
                "internalDate": detail.get("internalDate"),
            }
        )
    return messages


def mark_messages_read(message_ids: List[str]) -> int:
    if not message_ids:
        return 0
    service = _load_gmail_service()
    body = {"removeLabelIds": ["UNREAD"], "ids": message_ids}
    resp = (
        service.users()
        .messages()
        .batchModify(userId="me", body=body)
        .execute()
    )
    # Gmail batchModify does not return count; return requested count for now.
    logger.info("[EmailMarkRead] Requested mark-read for %d messages", len(message_ids))
    return len(message_ids)


def search_messages_by_criteria(
    sender: Optional[str],
    topic: Optional[str],
    days_back: int = 14,
    max_items: int = 20,
    unread_only: bool = True,
) -> List[Dict]:
    service = _load_gmail_service()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    query = _build_query(int(cutoff.timestamp()), None, sender, topic, unread_only)
    resp = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_items)
        .execute()
    )
    ids = resp.get("messages", [])
    results: List[Dict] = []
    for msg in ids:
        detail = (
            service.users()
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
        results.append(
            {
                "id": msg["id"],
                "threadId": detail.get("threadId"),
                "from": header_map.get("From", ""),
                "subject": header_map.get("Subject", ""),
                "snippet": detail.get("snippet", ""),
                "internalDate": detail.get("internalDate"),
            }
        )
    return results


def fetch_full_message(message_id: str) -> Dict:
    service = _load_gmail_service()
    detail = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )
    payload = detail.get("payload", {})
    headers = payload.get("headers", [])
    header_map = {h["name"]: h["value"] for h in headers}
    body = ""
    if "data" in payload.get("body", {}):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode(errors="ignore")
    elif payload.get("parts"):
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode(errors="ignore")
                break
    return {
        "id": message_id,
        "threadId": detail.get("threadId"),
        "from": header_map.get("From", ""),
        "to": header_map.get("To", ""),
        "subject": header_map.get("Subject", ""),
        "body": body,
        "snippet": detail.get("snippet", ""),
        "internalDate": detail.get("internalDate"),
    }


def send_reply(original_message_id: str, reply_text: str) -> str:
    """
    Best-effort reply; may fail without send scope in token.
    """
    service = _load_gmail_service()
    original = fetch_full_message(original_message_id)
    thread_id = original.get("threadId")
    to_addr = original.get("from")
    subject = original.get("subject") or ""
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    message = MIMEMultipart()
    message["To"] = to_addr
    message["Subject"] = subject
    message.attach(MIMEText(reply_text, "plain"))
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    resp = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": raw, "threadId": thread_id})
        .execute()
    )
    logger.info("Sent reply in thread %s", thread_id)
    return resp.get("id")
