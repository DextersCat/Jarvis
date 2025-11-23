"""
Shared Google API helper for Jarvis.
Provides simple client construction and status handling for multiple Google services.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

TOKEN_DIR = Path.home() / ".jarvis_tokens"

SERVICE_CONFIG = {
    "gmail": {
        "token": TOKEN_DIR / "gmail_token.json",
        "scopes": [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
        ],
        "version": "v1",
    },
    "calendar": {
        "token": TOKEN_DIR / "calendar_token.json",
        "scopes": ["https://www.googleapis.com/auth/calendar.readonly"],
        "version": "v3",
    },
    "tasks": {
        "token": TOKEN_DIR / "tasks_token.json",
        "scopes": ["https://www.googleapis.com/auth/tasks.readonly"],
        "version": "v1",
    },
    "docs": {
        "token": TOKEN_DIR / "docs_token.json",
        "scopes": ["https://www.googleapis.com/auth/documents.readonly"],
        "version": "v1",
    },
    "sheets": {
        "token": TOKEN_DIR / "sheets_token.json",
        "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"],
        "version": "v4",
    },
    "slides": {
        "token": TOKEN_DIR / "slides_token.json",
        "scopes": ["https://www.googleapis.com/auth/presentations.readonly"],
        "version": "v1",
    },
    "drive": {
        "token": TOKEN_DIR / "drive_token.json",
        "scopes": ["https://www.googleapis.com/auth/drive.metadata.readonly"],
        "version": "v3",
    },
    # Non-OAuth API key based (Custom Search, Places, Gemini/GenAI) are handled separately.
}


def load_credentials(token_path: Path, scopes: list) -> Credentials:
    if not token_path.exists():
        raise FileNotFoundError(f"Token missing: {token_path}")
    creds = Credentials.from_authorized_user_file(str(token_path), scopes)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError(f"Credentials invalid for {token_path}; re-auth required.")
    return creds


def build_service(name: str) -> object:
    cfg = SERVICE_CONFIG.get(name)
    if not cfg:
        raise ValueError(f"Unknown service: {name}")
    creds = load_credentials(cfg["token"], cfg["scopes"])
    return build(name, cfg["version"], credentials=creds, cache_discovery=False)


def check_oauth_service(name: str, call_fn) -> Dict:
    cfg = SERVICE_CONFIG.get(name, {})
    token = cfg.get("token")
    scopes = cfg.get("scopes")
    try:
        service = build_service(name)
        result = call_fn(service)
        return {"status": "PASS", "detail": result}
    except FileNotFoundError:
        return {"status": "NOT CONFIGURED", "detail": f"Missing token: {token}"}
    except RuntimeError as exc:
        txt = str(exc)
        if "insufficient" in txt.lower() or "invalid_scope" in txt.lower():
            return {"status": "INSUFFICIENT SCOPE", "detail": txt}
        return {"status": "FAIL", "detail": txt}
    except HttpError as exc:
        content = getattr(exc, "content", b"")
        detail = content.decode() if content else str(exc)
        if "insufficient" in detail.lower() or "invalid_scope" in detail.lower():
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
    except Exception as exc:  # noqa: BLE001
        return {"status": "FAIL", "detail": repr(exc)}


def check_gemini(name: str = "gemini") -> Dict:
    api_key = os.getenv("GOOGLE_GENAI_API_KEY")
    if not api_key:
        return {"status": "NOT CONFIGURED", "detail": "Missing GOOGLE_GENAI_API_KEY"}
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-pro")
        res = model.generate_content("Health check ping from Jarvis.")
        text = res.text if hasattr(res, "text") else str(res)
        return {"status": "PASS", "detail": f"len={len(text)}"}
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).lower()
        if "permission" in msg or "scope" in msg:
            return {"status": "INSUFFICIENT SCOPE", "detail": repr(exc)}
        return {"status": "FAIL", "detail": repr(exc)}
