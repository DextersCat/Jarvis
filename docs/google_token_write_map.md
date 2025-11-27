# Google Token Write Map (Jarvis Brain)

Write locations (as of this change):
- `services/google_helper.py` — `_persist_credentials(service, token_path, creds, context)` (used on refresh/load). Uses `creds.to_json()` with guardrails.
- `tools/google_oauth_flow.py` — saves initial tokens after OAuth flow using `creds.to_json()` with expiry guard.

Search checks:
- No other writers found for `*.jarvis_tokens/*_token.json` (grep for `write_text(` and `_token.json`).

Notes:
- Guardrails refuse to persist tokens whose `expiry <= now`; warn if expiry is None.
- All writes go through `creds.to_json()`; no manual expiry computation remains.
