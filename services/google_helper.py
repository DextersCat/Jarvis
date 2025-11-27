"""
Shared Google API helper for Jarvis.
Provides simple client construction and status handling for multiple Google services.
Standardises token loading, refresh, and persistence using google.oauth2.credentials.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple
import urllib.error
import urllib.request

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

TOKEN_DIR = Path.home() / ".jarvis_tokens"
CREDENTIALS_FILE = TOKEN_DIR / "credentials.json"

SERVICE_SCOPES = {
    "gmail": [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.send",
    ],
    "calendar": [
        "https://www.googleapis.com/auth/calendar",
    ],
    "tasks": [
        "https://www.googleapis.com/auth/tasks",
    ],
    "drive": [
        "https://www.googleapis.com/auth/drive",
    ],
    "docs": [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive",
    ],
    "sheets": [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ],
    "slides": [
        "https://www.googleapis.com/auth/presentations",
        "https://www.googleapis.com/auth/drive",
    ],
}

SERVICE_CONFIG = {
    "gmail": {
        "token": TOKEN_DIR / "gmail_token.json",
        "scopes": SERVICE_SCOPES["gmail"],
        "version": "v1",
    },
    "calendar": {
        "token": TOKEN_DIR / "calendar_token.json",
        "scopes": SERVICE_SCOPES["calendar"],
        "version": "v3",
    },
    "tasks": {
        "token": TOKEN_DIR / "tasks_token.json",
        "scopes": SERVICE_SCOPES["tasks"],
        "version": "v1",
    },
    "docs": {
        "token": TOKEN_DIR / "docs_token.json",
        "scopes": SERVICE_SCOPES["docs"],
        "version": "v1",
    },
    "sheets": {
        "token": TOKEN_DIR / "sheets_token.json",
        "scopes": SERVICE_SCOPES["sheets"],
        "version": "v4",
    },
    "slides": {
        "token": TOKEN_DIR / "slides_token.json",
        "scopes": SERVICE_SCOPES["slides"],
        "version": "v1",
    },
    "drive": {
        "token": TOKEN_DIR / "drive_token.json",
        "scopes": SERVICE_SCOPES["drive"],
        "version": "v3",
    },
    # Non-OAuth API key based (Custom Search, Places, Gemini/GenAI) are handled separately.
}


def get_service_config(name: str) -> Dict:
    cfg = SERVICE_CONFIG.get(name)
    if not cfg:
        raise ValueError(f"Unknown service: {name}")
    return cfg


def _persist_credentials(service: str, token_path: Path, creds: Credentials, context: str) -> None:
    """
    Persist credentials to disk using canonical JSON format.
    Guardrail: refuse to overwrite with a born-expired token.
    This function MUST be called with the current creds object (post-refresh/OAuth),
    otherwise stale expiry values could be persisted.
    """
    token_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    expiry = getattr(creds, "expiry", None)
    if expiry is None:
        logger.warning(
            "[GOOGLE_AUTH] Expiry is None for %s; writing token but re-auth may be needed. path=%s context=%s",
            service,
            token_path,
            context,
        )
    else:
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if expiry <= now:
            logger.error(
                "[GOOGLE_AUTH] Refusing to persist token for %s because expiry <= now (expiry=%s, now=%s) path=%s context=%s",
                service,
                expiry.isoformat(),
                now.isoformat(),
                token_path,
                context,
            )
            raise RuntimeError(
                f"Refusing to persist Google token for {service}: expiry {expiry.isoformat()} is not in the future."
            )
    token_path.write_text(creds.to_json(), encoding="utf-8")
    logger.info(
        "[GOOGLE_AUTH] Persisted credentials for %s to %s (expiry=%s, context=%s)",
        service,
        token_path,
        expiry.isoformat() if expiry else "None",
        context,
    )


def load_credentials(name: str) -> Credentials:
    """Load credentials for a service, refresh if needed, and persist on success."""
    cfg = get_service_config(name)
    token_path = cfg["token"]
    scopes = cfg["scopes"]
    if not token_path.exists():
        raise FileNotFoundError(f"Token missing: {token_path}")

    creds = Credentials.from_authorized_user_file(str(token_path), scopes)
    refresh_token_present = bool(creds.refresh_token)
    try:
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                logger.info(
                    "[GOOGLE_AUTH] Refreshing token for %s (expired=%s, has_refresh=%s)",
                    name,
                    creds.expired,
                    refresh_token_present,
                )
                creds.refresh(Request())
                _persist_credentials(name, token_path, creds, context="refresh")
            else:
                raise RuntimeError(
                    f"Credentials invalid for {token_path}; re-auth required (has_refresh={refresh_token_present})."
                )
        else:
            _persist_credentials(name, token_path, creds, context="load_valid")
    except Exception as exc:  # noqa: BLE001
        msg = str(exc)
        if "invalid_grant" in msg.lower():
            logger.error(
                "[GOOGLE_AUTH] invalid_grant refreshing %s (token=%s, has_refresh=%s)",
                name,
                token_path,
                refresh_token_present,
            )
            raise RuntimeError(
                f"Google auth for {name} failed: invalid_grant. Re-authorization required."
            ) from exc
        raise

    return creds


def build_service(name: str) -> object:
    cfg = get_service_config(name)
    creds = load_credentials(name)
    return build(name, cfg["version"], credentials=creds, cache_discovery=False)


def check_oauth_service(name: str, call_fn) -> Dict:
    cfg = SERVICE_CONFIG.get(name, {})
    token = cfg.get("token")
    try:
        service = build_service(name)
        result = call_fn(service)
        return {"status": "PASS", "detail": result}
    except FileNotFoundError:
        return {"status": "NOT CONFIGURED", "detail": f"Missing token: {token}"}
    except RuntimeError as exc:
        txt = str(exc)
        if "invalid_scope" in txt.lower() or "insufficient" in txt.lower():
            return {"status": "INSUFFICIENT SCOPE", "detail": txt}
        if "invalid_grant" in txt.lower():
            return {"status": "REAUTH REQUIRED", "detail": txt}
        return {"status": "FAIL", "detail": txt}
    except HttpError as exc:
        content = getattr(exc, "content", b"")
        detail = content.decode() if content else str(exc)
        if "invalid_scope" in detail.lower() or "insufficient" in detail.lower():
            return {"status": "INSUFFICIENT SCOPE", "detail": detail}
        return {"status": "FAIL", "detail": detail}
    except Exception as exc:  # noqa: BLE001
        return {"status": "FAIL", "detail": repr(exc)}


def check_api_key_service(name: str, required_envs: Tuple[str, ...], call_fn) -> Dict:
    missing = [env for env in required_envs if not os.getenv(env)]
    if missing:
        return {"status": "NOT CONFIGURED", "detail": f"Missing env: {', '.join(missing)}"}
    try:
        result = call_fn()
        return {"status": "PASS", "detail": result}
    except urllib.error.HTTPError as exc:
        content = exc.read()
        detail = content.decode(errors="ignore") if content else str(exc)
        return {"status": "FAIL", "detail": f"{exc.code} {detail}"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "FAIL", "detail": repr(exc)}


def check_gemini(name: str = "gemini") -> Dict:
    api_key = os.getenv("GOOGLE_GENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"status": "NOT CONFIGURED", "detail": "Missing GOOGLE_GENAI_API_KEY"}
    try:
        import json
        import urllib.request

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                body = resp.read()
                data = json.loads(body.decode("utf-8")) if body else {}
                models = data.get("models", []) if isinstance(data, dict) else []
                return {"status": "PASS", "detail": f"models={len(models)}"}
        except urllib.error.HTTPError as exc:
            content = exc.read()
            detail = content.decode(errors="ignore") if content else str(exc)
            return {"status": "FAIL", "detail": f"{exc.code} {detail}"}
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).lower()
        if "permission" in msg or "scope" in msg or "403" in msg:
            return {"status": "INSUFFICIENT SCOPE", "detail": repr(exc)}
        return {"status": "FAIL", "detail": repr(exc)}
