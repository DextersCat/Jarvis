#!/usr/bin/env python3
"""
Google OAuth flow helper for Jarvis services.
Usage:
  python3 tools/google_oauth_flow.py --service tasks
Supported services (token paths in ~/.jarvis_tokens):
  gmail, calendar, tasks, docs, sheets, slides, drive

Requires: ~/.jarvis_tokens/credentials.json (client secrets) unless overridden via --credentials.
"""

import argparse
import sys
from pathlib import Path
import os

from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.google_helper import get_service_config  # noqa: E402


def run_flow(service: str, credentials_file: Path):
    # Allow localhost HTTP redirect for installed apps (same as existing Gmail/Calendar flow).
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
    cfg = get_service_config(service)
    scopes = cfg["scopes"]
    token_path: Path = cfg["token"]
    token_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[{service}] Using client secrets: {credentials_file}")
    print(f"[{service}] Scopes: {scopes}")
    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), scopes=scopes)
    # Use console flow (same installed-app pattern; shows URL + asks for code).
    creds = flow.run_console(prompt="consent")
    token_path.write_text(creds.to_json())
    print(f"[{service}] Saved token to {token_path}")


def main():
    parser = argparse.ArgumentParser(description="Jarvis Google OAuth helper")
    parser.add_argument(
        "--service",
        required=True,
        choices=["gmail", "calendar", "tasks", "docs", "sheets", "slides", "drive"],
        help="Service to authorize",
    )
    parser.add_argument(
        "--credentials",
        default=str(Path.home() / ".jarvis_tokens" / "credentials.json"),
        help="Path to client secrets JSON (default: ~/.jarvis_tokens/credentials.json)",
    )
    args = parser.parse_args()
    credentials_file = Path(args.credentials)
    if not credentials_file.exists():
        print(f"Credentials file missing: {credentials_file}")
        return 1
    run_flow(args.service, credentials_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
