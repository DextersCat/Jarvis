# Google Integration Matrix — 2025-11-23

| API | Intended Usage / Modules | Status | Test Command or Utterance | Notes |
| --- | --- | --- | --- | --- |
| Gmail | services/email_service.py, brain email handlers | PASS | `python3 diagnostics/google_services_check.py` (gmail) / “Summarize my emails” | Token at ~/.jarvis_tokens/gmail_token.json; scopes read+modify; diag fetched unread IDs. |
| Calendar | services/calendar_service.py, brain calendar handler | PASS | `python3 diagnostics/google_services_check.py` (calendar) / “Summarize my calendar for today.” | Token at ~/.jarvis_tokens/calendar_token.json; scopes calendar.readonly; diag fetched events. |
| Tasks | (not implemented yet) | NOT CONFIGURED | `python3 diagnostics/google_services_check.py` (tasks) | Missing token: ~/.jarvis_tokens/tasks_token.json; no Tasks module/handler. |
| Docs | (not implemented yet) | NOT CONFIGURED | `python3 diagnostics/google_services_check.py` (docs) | Missing token: ~/.jarvis_tokens/docs_token.json; no Docs module/handler. |
| Sheets | (not implemented yet) | NOT CONFIGURED | `python3 diagnostics/google_services_check.py` (sheets) | Missing token: ~/.jarvis_tokens/sheets_token.json; no Sheets module/handler. |
| Slides | (not implemented yet) | NOT CONFIGURED | `python3 diagnostics/google_services_check.py` (slides) | Missing token: ~/.jarvis_tokens/slides_token.json; no Slides module/handler. |
| Drive | (not implemented yet) | NOT CONFIGURED | `python3 diagnostics/google_services_check.py` (drive) | Missing token: ~/.jarvis_tokens/drive_token.json; no Drive module/handler. |
| Custom Search (CSE) | services/search_service.py (Programmable Search) | NOT CONFIGURED | `python3 diagnostics/google_services_check.py` (custom_search) | Missing env: GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_CX. |
| Gemini | (not wired into brain) | NOT CONFIGURED | `python3 diagnostics/google_services_check.py` (gemini) | Missing env: GOOGLE_GENAI_API_KEY; no current usage in brain. |
