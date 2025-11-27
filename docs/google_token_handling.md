# Google OAuth Token Handling (Jarvis Brain)

## Token locations
- Client secrets: `~/.jarvis_tokens/credentials.json`
- Tokens per service (persisted JSON via `Credentials.to_json()`):
  - Gmail: `~/.jarvis_tokens/gmail_token.json`
  - Calendar: `~/.jarvis_tokens/calendar_token.json`
  - Tasks: `~/.jarvis_tokens/tasks_token.json`
  - Docs: `~/.jarvis_tokens/docs_token.json`
  - Sheets: `~/.jarvis_tokens/sheets_token.json`
  - Slides: `~/.jarvis_tokens/slides_token.json`
  - Drive: `~/.jarvis_tokens/drive_token.json`

## How tokens are loaded and refreshed
- Shared helper: `services/google_helper.py`
- Load: `Credentials.from_authorized_user_file(token_path, scopes)`
- If invalid:
  - If expired **and** `refresh_token` present: refresh with `Request()`, then persist back to disk via `creds.to_json()`.
  - Else: raise `RuntimeError` with “re-auth required”.
- On `invalid_grant` during refresh: log and raise `RuntimeError("Google auth for <service> failed: invalid_grant. Re-authorization required.")`.
- Services call `google_helper.build_service(<name>)`, which uses the above and builds the discovery client with `cache_discovery=False`.

## Canonical scopes (see `SERVICE_CONFIG` in `services/google_helper.py`)
- Gmail: `gmail.readonly`, `gmail.modify`
- Calendar: `calendar.readonly`
- Tasks: `tasks.readonly`
- Docs: `documents.readonly`
- Sheets: `spreadsheets.readonly`
- Slides: `presentations.readonly`
- Drive: `drive.metadata.readonly`

## Re-auth flow
- Use `tools/google_oauth_flow.py --service <name>` (defaults to `~/.jarvis_tokens/credentials.json`).
- Flow runs InstalledAppFlow, prompts consent with `prompt=consent`, `access_type=offline`, `include_granted_scopes=False`, redirect `http://localhost:8080/`.
- After success, the tool writes the token JSON (including refresh_token and expiry) to the service token path.

## Operational notes
- After a successful refresh, the helper writes the updated credentials back to disk so expiry stays current.
- If refresh fails with `invalid_grant`, do **not** overwrite the token; re-authorize that service.
- Services must not manually serialize credentials; rely on `Credentials.to_json()`/`from_authorized_user_file()`.
- Error messaging:
  - Missing token: “Missing token: <path>”
  - Invalid scope: “INSUFFICIENT SCOPE”
  - `invalid_grant`: “REAUTH REQUIRED”

## Quick test commands
- Diagnostics: `python3 diagnostics/google_services_check.py` (uses shared helper).
- Service-specific (from Jarvis brain):
  - Gmail: “Summarize my emails.”
  - Calendar: “Summarize my calendar for today.”
  - Tasks: “Summarize my tasks.” (if handler present)

## What to do on failure
- `invalid_grant`: run `tools/google_oauth_flow.py --service <name>` to re-auth and replace the token file.
- `INSUFFICIENT SCOPE`: re-auth with scopes matching `SERVICE_CONFIG`.
- Persisted expiry in the token JSON must be in the future; if not, re-auth and ensure the new token is written.

## Implementation notes (write path)
- All token writes funnel through:
  - `services/google_helper._persist_credentials` (post-refresh or validated load).
  - `tools/google_oauth_flow.py` (initial OAuth).
- Guardrail: tokens are refused if `expiry <= now`; a warning is logged if expiry is missing. Writes use `creds.to_json()` only.
- Logs to check: `[GOOGLE_AUTH] Persisted credentials ... (expiry=...)` or refusal messages.
