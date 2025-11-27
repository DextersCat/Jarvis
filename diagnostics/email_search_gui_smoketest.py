"""
Email search + HUD GUI smoke test for Phase 4.6.

This script runs a real email.search_emails_by_query via EmailAgent,
then forwards the results to the HUD reply-options endpoint so the
GUI can render the collapsible search results panel.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import requests

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from agents.email_agent import EmailAgent  # noqa: E402


HUD_REPLY_OPTIONS_URL = "http://localhost:5000/api/jarvis/reply-options"


def main() -> None:
    agent = EmailAgent()
    intent = {
        "domain": "email",
        "action": "search_emails_by_query",
        "query": "Pi Vision",
        "max_results": 5,
    }

    print(f"[TEST] Running email search intent: {intent}")
    result = agent.execute(intent)

    messages = (result.get("data") or {}).get("messages") or []
    print(f"[TEST] Result status: {result.get('status')} success={result.get('success')}")
    print(f"[TEST] Messages returned: {len(messages)}")
    for idx, msg in enumerate(messages):
        print(
            f"  {idx+1}. subject='{msg.get('subject','')}' from='{msg.get('from','')}' "
            f"date='{msg.get('date') or msg.get('received_at','')}'"
        )

    payload = {
        "domain": "email",
        "action": "search_emails_by_query",
        "query": intent["query"],
        "question_id": f"smoketest_{uuid.uuid4().hex[:8]}",
        "data": {
            "messages": messages,
        },
    }

    try:
        resp = requests.post(HUD_REPLY_OPTIONS_URL, json=payload, timeout=5)
        resp.raise_for_status()
        print(f"[TEST] Sent to HUD reply-options endpoint ({HUD_REPLY_OPTIONS_URL}); status={resp.status_code}")
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Failed to send HUD payload: {exc}")


if __name__ == "__main__":
    main()
