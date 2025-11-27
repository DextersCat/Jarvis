"""
EmailAgent skeleton for Jarvis v3.

Conforms to the standard agent interface described in:
- docs/JARVIS3_MASTER_ARCHITECTURE.md
- Phase 4, step 4.1 in docs/JARVIS3_TODO_ROADMAP.md

This agent only declares capabilities and intent handling stubs.
No Gmail or external integrations are implemented here.
"""

import base64
from typing import Any, Dict, Optional

from email.mime.text import MIMEText
from services import google_helper


class EmailAgent:
    """Minimal email agent that advertises the email domain and intent hooks."""

    DOMAIN = "email"

    def can_handle(self, intent: Dict[str, Any]) -> bool:
        """
        Return True if this agent can handle the given intent.

        Expected intent format (placeholder):
        {
            "domain": "email",
            "action": "<action>",
            ...
        }
        """
        if not intent:
            return False
        return intent.get("domain") == self.DOMAIN and intent.get("action") in {
            "read_last_email_from",
            "reply_to_last_email",
            "summarize_inbox_state",
            "search_emails_by_query",
        }

    def execute(self, intent: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Execute the intent using the provided context.

        Supports:
        - read_last_email_from: fetch latest Gmail message from given sender.
        - reply_to_last_email: reply to the latest email in a thread or from sender.
        - summarize_inbox_state: inbox counts and recent emails.
        - search_emails_by_query: search Gmail with a query string.
        """
        action = intent.get("action")
        if action == "read_last_email_from":
            sender = intent.get("parameters", {}).get("sender")
            return self._read_last_email_from(sender)
        if action == "reply_to_last_email":
            params = intent.get("parameters", {})
            body = params.get("body")
            sender = params.get("sender")
            thread_id = params.get("thread_id")
            if not body or (not sender and not thread_id):
                return {"success": False, "status": "error", "reason": "missing_sender_or_thread_id"}
            return self._reply_to_last_email(body=body, sender=sender, thread_id=thread_id)
        if action == "summarize_inbox_state":
            params = intent.get("parameters", {}) or {}
            max_results = params.get("max_results", 10)
            try:
                max_results = int(max_results)
            except (TypeError, ValueError):
                max_results = 10
            max_results = max(1, min(max_results, 50))
            try:
                svc = google_helper.build_service("gmail")
            except Exception as exc:  # noqa: BLE001
                return {
                    "status": "error",
                    "error_type": "gmail_service_error",
                    "message": str(exc),
                }
            return self._summarize_inbox_state(svc, max_results)
        if action == "search_emails_by_query":
            query = intent.get("query")
            if not isinstance(query, str) or not query.strip():
                return {
                    "status": "error",
                    "error": "missing_query",
                    "message": "Query must be a non-empty string.",
                }

            raw_max_results = intent.get("max_results", 10)
            try:
                max_results = int(raw_max_results)
            except (TypeError, ValueError):
                max_results = 10

            # If user gives 0 / negative, fall back to default first
            if max_results <= 0:
                max_results = 10

            # Clamp into [1, 50] as per roadmap
            max_results = max(1, min(max_results, 50))

            svc = google_helper.build_service("gmail")
            return self._search_emails_by_query(svc, query.strip(), max_results)

        return {
            "success": False,
            "action": action,
            "domain": self.DOMAIN,
            "details": {"message": "Unsupported action"},
        }

    def describe_capabilities(self) -> Dict[str, Any]:
        """
        Describe what this agent is intended to handle.

        Placeholder list aligned with email-domain intents (send/read/mark/etc.).
        """
        return {
            "domain": self.DOMAIN,
            "intents": [
                "read_last_email_from",
                "reply_to_last_email",
                "summarize_inbox_state",
                "search_emails_by_query",
            ],
            "status": "skeleton",
            "notes": "Implements read_last_email_from, reply_to_last_email, summarize_inbox_state; other actions are TODO.",
            "capability_details": [
                {
                    "action": "summarize_inbox_state",
                    "description": "Summarize Gmail inbox: unread counts, important/starred counts, and recent messages.",
                    "parameters": {
                        "max_results": {
                            "type": "int",
                            "required": False,
                            "default": 10,
                            "description": "Maximum recent emails to include (1-50).",
                        }
                    },
                },
                {
                    "action": "search_emails_by_query",
                    "description": "Search Gmail using a query string and list matching messages.",
                    "parameters": {
                        "query": {
                            "type": "string",
                            "required": True,
                            "description": "Gmail search query (e.g., from:foo is:unread).",
                        },
                        "max_results": {
                            "type": "int",
                            "required": False,
                            "default": 10,
                            "description": "Maximum results to return (1-50).",
                        },
                    },
                }
            ],
        }

    def _read_last_email_from(self, sender: Optional[str]) -> Dict[str, Any]:
        """Fetch the newest Gmail message from the specified sender."""
        if not sender:
            return {"success": False, "status": "not_found", "details": {"message": "No sender provided"}}
        try:
            svc = google_helper.build_service("gmail")
            query = f"from:{sender}"
            resp = (
                svc.users()
                .messages()
                .list(userId="me", q=query, maxResults=1)
                .execute()
            )
            ids = resp.get("messages", [])
            if not ids:
                return {"success": True, "status": "not_found", "from": sender}
            msg_id = ids[0]["id"]
            detail = (
                svc.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )
            headers = detail.get("payload", {}).get("headers", [])
            header_map = {h["name"]: h["value"] for h in headers}
            subject = header_map.get("Subject", "(no subject)")
            snippet = detail.get("snippet", "")
            internal_ts = detail.get("internalDate")
            body = self._extract_plain_text(detail.get("payload", {}))
            return {
                "success": True,
                "status": "ok",
                "from": sender,
                "subject": subject,
                "snippet": snippet,
                "body": body,
                "timestamp": internal_ts,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "success": False,
                "status": "error",
                "from": sender,
                "details": {"message": str(exc)},
            }

    def _extract_plain_text(self, payload: Dict[str, Any]) -> str:
        """Extract text/plain part from Gmail message payload."""
        if not payload:
            return ""
        mime_type = payload.get("mimeType", "")
        if mime_type == "text/plain" and payload.get("body", {}).get("data"):
            import base64

            return base64.urlsafe_b64decode(payload["body"]["data"]).decode(errors="ignore")
        parts = payload.get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                import base64

                return base64.urlsafe_b64decode(part["body"]["data"]).decode(errors="ignore")
        return ""

    def _reply_to_last_email(self, body: str, sender: Optional[str], thread_id: Optional[str]) -> Dict[str, Any]:
        """Reply to latest email in a thread or from a sender."""
        try:
            svc = google_helper.build_service("gmail")
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "status": "error", "reason": str(exc)}

        original = None
        if thread_id:
            try:
                thread = svc.users().threads().get(userId="me", id=thread_id, format="metadata", metadataHeaders=["From", "To", "Subject"]).execute()
                msgs = thread.get("messages", [])
                if msgs:
                    original = msgs[-1]
            except Exception as exc:  # noqa: BLE001
                return {"success": False, "status": "error", "reason": str(exc)}
        elif sender:
            query = f"from:{sender}"
            try:
                resp = svc.users().messages().list(userId="me", q=query, maxResults=1).execute()
                ids = resp.get("messages", [])
                if ids:
                    original = svc.users().messages().get(userId="me", id=ids[0]["id"], format="metadata", metadataHeaders=["From", "To", "Subject", "Thread-Id"]).execute()
            except Exception as exc:  # noqa: BLE001
                return {"success": False, "status": "error", "reason": str(exc)}

        if not original:
            return {"success": True, "status": "not_found", "from": sender, "thread_id": thread_id}

        headers = original.get("payload", {}).get("headers", [])
        header_map = {h["name"]: h["value"] for h in headers}
        orig_from = header_map.get("From", "")
        orig_subject = header_map.get("Subject", "(no subject)")
        orig_thread_id = original.get("threadId") or thread_id
        to_addr = orig_from
        subject = orig_subject if orig_subject.lower().startswith("re:") else f"Re: {orig_subject}"

        msg = MIMEText(body)
        msg["To"] = to_addr
        msg["Subject"] = subject
        if orig_thread_id:
            msg["In-Reply-To"] = original.get("id")
            msg["References"] = original.get("id")

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        try:
            resp = svc.users().messages().send(userId="me", body={"raw": raw, "threadId": orig_thread_id}).execute()
            return {
                "success": True,
                "status": "sent",
                "to": to_addr,
                "subject": subject,
                "thread_id": orig_thread_id,
                "original_message_id": original.get("id"),
                "sent_message_id": resp.get("id"),
            }
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "status": "error", "reason": str(exc)}

    def _summarize_inbox_state(self, svc, max_results: int) -> Dict[str, Any]:
        """Summarize inbox counts and recent emails."""
        try:
            unread_resp = (
                svc.users()
                .messages()
                .list(userId="me", q="is:unread", includeSpamTrash=False, maxResults=1)
                .execute()
            )
            unread_count = unread_resp.get("resultSizeEstimate", 0)

            imp_star_resp = (
                svc.users()
                .messages()
                .list(userId="me", q="is:important OR is:starred", includeSpamTrash=False, maxResults=1)
                .execute()
            )
            important_or_starred_count = imp_star_resp.get("resultSizeEstimate", 0)

            recent_resp = (
                svc.users()
                .messages()
                .list(userId="me", maxResults=max_results, includeSpamTrash=False)
                .execute()
            )
            ids = recent_resp.get("messages", []) or []
            recent_emails = []
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
                recent_emails.append(
                    {
                        "id": msg.get("id"),
                        "thread_id": detail.get("threadId"),
                        "from": header_map.get("From", ""),
                        "subject": header_map.get("Subject", ""),
                        "received_at": header_map.get("Date", ""),
                    }
                )

            return {
                "success": True,
                "status": "ok",
                "action": "summarize_inbox_state",
                "summary": {
                    "unread_count": unread_count,
                    "important_or_starred_count": important_or_starred_count,
                    "recent_emails": recent_emails,
                },
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "success": False,
                "status": "error",
                "action": "summarize_inbox_state",
                "error_type": "gmail_api_error",
                "message": str(exc),
            }

    def _search_emails_by_query(self, svc, query: str, max_results: int) -> Dict[str, Any]:
        """Search Gmail using a query string and list matching messages."""
        try:
            resp = (
                svc.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )
            msgs = resp.get("messages", []) or []
            total_estimate = resp.get("resultSizeEstimate", 0)
            if not msgs:
                return {
                    "success": True,
                    "status": "not_found",
                    "summary": f"No emails matched query: {query!r}",
                    "data": {"query": query, "total_matched": 0, "messages": []},
                }

            results = []
            for msg in msgs[:max_results]:
                detail = (
                    svc.users()
                    .messages()
                    .get(
                        userId="me",
                        id=msg["id"],
                        format="metadata",
                        metadataHeaders=["Subject", "From", "Date"],
                    )
                    .execute()
                )
                headers = detail.get("payload", {}).get("headers", [])
                header_map = {h["name"]: h["value"] for h in headers}
                results.append(
                    {
                        "id": msg.get("id"),
                        "thread_id": detail.get("threadId"),
                        "subject": header_map.get("Subject", ""),
                        "from": header_map.get("From", ""),
                        "date": header_map.get("Date", ""),
                        "snippet": detail.get("snippet", ""),
                    }
                )

            return {
                "success": True,
                "status": "ok",
                "action": "search_emails_by_query",
                "summary": f"Found {len(results)} email(s) (estimate: {total_estimate}) for query {query!r}.",
                "data": {
                    "query": query,
                    "total_matched": int(total_estimate),
                    "max_results": max_results,
                    "messages": results,
                },
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "success": False,
                "status": "error",
                "action": "search_emails_by_query",
                "error": str(exc),
            }
