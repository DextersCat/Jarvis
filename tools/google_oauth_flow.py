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
    # Align with existing Gmail/Calendar flow: explicit localhost redirect for installed apps.
    flow.redirect_uri = "http://localhost:8080/"
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline", include_granted_scopes="true")
    print("\n== COPY THIS URL INTO YOUR BROWSER TO AUTHORIZE ==\n")
    print(auth_url)
    print("\nAfter approving, paste the full redirect URL here.\n")
    redirect_response = input("Redirect URL: ").strip()
    flow.fetch_token(authorization_response=redirect_response)
    creds = flow.credentials
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
