import json
import logging
import re
import ast
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

CLASSIFY_SYSTEM_PROMPT = (
    "You are Jarvis classifying emails. "
    "Given sender, subject, snippet, and date, return categories (list of short labels), "
    "importance_score 0.0-1.0, and boolean flags: contains_invoice, contains_order_update, "
    "contains_problem_indicator, contains_action_items, has_links, has_attachments."
)

PREFS_PATH = Path("/mnt/f/JARVIS_LIBRARY/config/email_preferences.json")


def _load_preferences() -> Dict:
    if not PREFS_PATH.exists():
        return {}
    try:
        return json.loads(PREFS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("[EmailPrefs] Failed to load preferences: %s", exc)
        return {}


def _apply_preferences(classification: Dict, email: Dict) -> Dict:
    prefs = _load_preferences()
    sender_rules = prefs.get("sender_rules", []) if isinstance(prefs, dict) else []
    sender = (email.get("from") or email.get("sender") or "").lower()
    updated = classification.copy()
    for rule in sender_rules:
        pattern = (rule.get("pattern") or "").lower()
        if pattern and pattern in sender:
            if "importance_override" in rule:
                updated["importance_score"] = float(rule["importance_override"])
            tags_add = rule.get("tags_add") or []
            if tags_add:
                merged = set(updated.get("categories", [])) | set(tags_add)
                updated["categories"] = list(merged)
            logger.info("[EmailPrefs] Applied sender rule %s to message %s", pattern, email.get("id"))
    return updated


def classify_email(llm_client, email: Dict) -> Dict:
    """
    Returns classification dict with categories, importance_score, flags.
    If classification fails, returns sensible defaults.
    """
    defaults = {
        "categories": [],
        "importance_score": 0.3,
        "contains_invoice": False,
        "contains_order_update": False,
        "contains_problem_indicator": False,
        "contains_action_items": False,
        "has_links": False,
        "has_attachments": False,
    }
    if not llm_client:
        return defaults

    sender = email.get("from") or email.get("sender") or ""
    subject = email.get("subject", "")
    snippet = email.get("snippet", "")
    received_at = email.get("received_at", "")

    user_content = (
        f"Sender: {sender}\n"
        f"Subject: {subject}\n"
        f"Date: {received_at}\n"
        f"Snippet: {snippet}\n"
        "Respond in JSON with keys: categories (list of strings), importance_score (float), "
        "contains_invoice, contains_order_update, contains_problem_indicator, contains_action_items, "
        "has_links, has_attachments (all booleans). Keep it short."
    )

    try:
        completion = llm_client.chat.completions.create(
            model="llama3",
            messages=[
                {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0,
        )
        content = completion.choices[0].message.content
        logger.info("[EmailClassify] raw response: %s", content)
        import json

        def _parse_json_payload(text: str) -> Dict:
            try:
                return json.loads(text)
            except Exception:
                match = re.search(r"\{.*\}", text, re.DOTALL)
                if match:
                    payload = match.group(0)
                    payload = (
                        payload.replace("False", "false")
                        .replace("True", "true")
                        .replace("None", "null")
                    )
                    try:
                        return json.loads(payload)
                    except Exception:
                        try:
                            return ast.literal_eval(payload)
                        except Exception:
                            pass
                raise

        data = _parse_json_payload(content)
        result = defaults.copy()
        result.update({
            "categories": data.get("categories", []),
            "importance_score": float(data.get("importance_score", 0.3)),
            "contains_invoice": bool(data.get("contains_invoice", False)),
            "contains_order_update": bool(data.get("contains_order_update", False)),
            "contains_problem_indicator": bool(data.get("contains_problem_indicator", False)),
            "contains_action_items": bool(data.get("contains_action_items", False)),
            "has_links": bool(data.get("has_links", False)),
            "has_attachments": bool(data.get("has_attachments", False)),
        })
        return _apply_preferences(result, email)
    except Exception as exc:
        logger.warning("[EmailClassify] classification failed: %s", exc)
        return defaults
