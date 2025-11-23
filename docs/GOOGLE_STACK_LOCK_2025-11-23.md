# Phase C3 Google Stack Lock-In — 2025-11-23

Status (diagnostics: `python3 diagnostics/google_services_check.py`)
- Gmail: PASS
- Calendar: PASS
- Tasks: PASS
- Docs: PASS
- Sheets: PASS
- Slides: PASS
- Drive: PASS
- Custom Search: PASS (status=200)
- Gemini: FAIL — PARKED (API_KEY_INVALID from generativelanguage.googleapis.com; external GCP/AI Studio fix required, no code changes)

Verification commands
- Full check: `python3 diagnostics/google_services_check.py`
- Custom Search focused: `python3 diagnostics/cse_key_check.py`

Secrets and tokens
- Env: `/root/JARVIS/.env` (git-ignored, canonical, controlled by Chairman; do not delete or auto-regenerate)
- Windows master copy: `C:\Users\spenc\JARVIS-Workspace\config\.env.txt`
- OAuth tokens: `~/.jarvis_tokens/*.json` (gmail, calendar, tasks, drive, docs, sheets, slides). Only explicit OAuth tooling may create/update these; never delete automatically.

Notes
- Gemini remains parked at 400 API_KEY_INVALID; requires resolving in Google console/AI Studio. Do not alter Gemini code until the key is fixed externally.
