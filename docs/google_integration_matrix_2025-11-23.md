# Google Integration Matrix — 2025-11-23

| API | Intended Usage / Modules | Status | Test Command or Utterance | Notes |
| --- | --- | --- | --- | --- |
| Gmail | services/email_service.py, brain email handlers | PASS | `python3 diagnostics/google_gmail_check.py` / “Summarize my emails” | Token at ~/.jarvis_tokens/gmail_token.json; scopes read+modify; diag fetched 5 unread IDs. |
| Calendar | services/calendar_service.py, brain calendar handler | PASS | `python3 diagnostics/google_calendar_check.py` / “Summarize my calendar for today.” | Token at ~/.jarvis_tokens/calendar_token.json; scopes calendar.readonly; diag fetched 5 events. |
| Tasks | No module found | UNUSED | n/a | No Tasks code present; requires future implementation/OAuth. |
| Docs | No module found | UNUSED | n/a | Not implemented. |
| Sheets | No module found | UNUSED | n/a | Not implemented. |
| Slides | No module found | UNUSED | n/a | Not implemented. |
| Drive | No module found | UNUSED | n/a | Not implemented. |
| Custom Search (CSE) | services/search_service.py (Programmable Search) | UNKNOWN | Not run (needs GOOGLE_SEARCH_API_KEY/GOOGLE_SEARCH_CX) | Code uses env vars; no keys present in env, so status not verified. |
