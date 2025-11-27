from __future__ import annotations

from typing import Dict, Optional, Tuple

# Natural LLM domain -> canonical Jarvis domain
DOMAIN_MAP: Dict[str, str] = {
    # Core canonical domains
    "calendar": "calendar",
    "email": "email",
    "docs": "docs",
    "search": "search",
    "system": "system",
    "reminder": "reminder",
    "memory": "memory",
    "robotics": "robotics",
    "vision": "vision",
    "tasks": "tasks",
    "filesystem": "filesystem",

    # Cycle-1/2/3/4 aliases
    "email_search": "email",
    "email_management": "email",
    "email_system": "email",
    "email_response": "email",

    "document_editing": "docs",
    "document_management": "docs",
    "document_storage": "docs",
    "doc_search": "docs",
    "doc_creation": "docs",
    "doc_management": "docs",
    "doc_editing": "docs",

    "audio_control": "system",
    "audio": "system",
    "browser_settings": "system",

    "presence_detection": "vision",

    "task_management": "tasks",
    "tech": "search",
}

# Per canonical domain, natural action -> canonical action
ACTION_MAP: Dict[str, Dict[str, str]] = {
    "calendar": {
        "list_reminders": "list_reminders",
        "get_upcoming_events": "list_events",
        "delete_event": "delete_event",
        "list_events": "list_events",
        "update_meeting": "update_meeting",
        "move_meeting": "move_event",
        "move_event": "move_event",
        "reschedule_event": "move_event",
        "get_schedule": "list_events",
        "get_events_by_date_range": "list_events",
    },
    "email": {
        "search_email": "search_email",
        "search_new_email": "search_email",
        "search_inbox": "search_email",
        "search_unread_email": "search_unread_email",
        "delete_last_email": "delete_email",
        "reply_email": "reply_email",
        "forward_email": "forward_email",
        "mark_as_read": "mark_read",
        "delete_unread_messages": "delete_email",
        "list_unread_email": "search_unread_email",
    },
    "docs": {
        "open_document": "open_document",
        "duplicate_file": "duplicate_document",
        "duplicate_document": "duplicate_document",
        "create_document": "create_document",
        "search_documents_by_query": "search_documents",
        "search_documents": "search_documents",
        "delete_document": "delete_document",
        "update_document_section": "update_document",
        "search_docx_by_phrase": "search_documents",
    },
    "search": {
        "web_search": "web_search",
        "image_search": "image_search",
        "search_for_news": "news_search",
        "compare_gpu_recommendation": "web_search",
    },
    "system": {
        "restart_process": "restart",
        "shutdown": "shutdown",
        "reboot": "restart",
        "set_volume": "set_volume",
        "get_available_memory": "get_system_status",
        "stop_conversation": "stop",
        "enable_feature": "enable_feature",
        "disable_bork_mode": "set_bork_mode_off",
        "set_bork_mode_off": "set_bork_mode_off",
    },
    "reminder": {
        "set_reminder": "set_reminder",
        "cancel_reminder": "delete_reminder",
        "delete_reminder": "delete_reminder",
        "create_reminder": "set_reminder",
    },
    "memory": {
        "forget_data": "delete_memory",
        "forget": "delete_memory",
        "update_memory_note": "update_memory",
        "recall_project_details": "query_memories",
        "retrieve_memory": "query_memories",
    },
    "robotics": {
        "stop_robot": "stop_robot",
        "perform_gesture": "run_routine",
        "spin_robot": "run_routine",
        "set_error_handling_mode": "set_bork_mode_on",
    },
    "vision": {
        "capture_image": "capture_snapshot",
        "take_photo": "capture_snapshot",
        "detect_object_position": "detect_presence",
        "get_current_presence": "detect_presence",
    },
    "tasks": {
        "create_note": "store_note",
    },
    "filesystem": {
        "list_files": "list_files",
        "duplicate_file": "duplicate_file",
    },
}

# CLARIFY MAP — Ambiguous / Unsafe / Missing Data
CLARIFY_MAP = {
    # Cycle-3 cases
    101: {"reason": "incomplete", "details": "email forwarding missing structure"},
    105: {"reason": "ambiguous", "details": "meeting reference unclear"},
    107: {"reason": "ambiguous", "details": "web GPU request unclear"},
    109: {"reason": "ambiguous", "details": "rename target unclear"},
    114: {"reason": "ambiguous", "details": "document list context missing"},
    116: {"reason": "ambiguous", "details": "memory retrieval unclear"},
    118: {"reason": "ambiguous", "details": "memory update incomplete"},
    130: {"reason": "unsafe", "details": "shutdown requires confirmation"},
    132: {"reason": "ambiguous", "details": "bork mode off unclear"},
    134: {"reason": "ambiguous", "details": "volume missing domain confirmation"},
    138: {"reason": "ambiguous", "details": "update doc section unclear"},
    139: {"reason": "ambiguous", "details": "news search unclear"},
    142: {"reason": "ambiguous", "details": "calendar request unclear"},
    143: {"reason": "ambiguous", "details": "reminder search incomplete"},
    146: {"reason": "ambiguous", "details": "open doc target unclear"},
    147: {"reason": "ambiguous", "details": "duplicate doc unclear"},
    150: {"reason": "ambiguous", "details": "memory lookup too vague"},
    151: {"reason": "ambiguous", "details": "note domain unclear"},
    155: {"reason": "ambiguous", "details": "document search context missing"},
    157: {"reason": "ambiguous", "details": "doc creation missing structure"},

    # Cycle-4 cases
    202: {"reason": "ambiguous", "details": "dentist appointment needs calendar reference"},
    203: {"reason": "ambiguous", "details": "reminder time unclear"},
    210: {"reason": "ambiguous", "details": "rename target ambiguous"},
    221: {"reason": "ambiguous", "details": "budget summary file unclear"},
    222: {"reason": "ambiguous", "details": "insert into plan unclear"},
    224: {"reason": "ambiguous", "details": "event context missing"},
    235: {"reason": "ambiguous", "details": "disk space domain unclear"},
    237: {"reason": "ambiguous", "details": "document creation incomplete"},
    238: {"reason": "ambiguous", "details": "which draft document?"},
    240: {"reason": "ambiguous", "details": "news search missing clarity"},
    241: {"reason": "ambiguous", "details": "image search target unclear"},
    244: {"reason": "ambiguous", "details": "reminder search too vague"},
    245: {"reason": "ambiguous", "details": "which dentist reminder?"},
    247: {"reason": "ambiguous", "details": "open roadmap: which one?"},
    248: {"reason": "ambiguous", "details": "duplicate target missing"},
    249: {"reason": "ambiguous", "details": "append target missing"},
    250: {"reason": "ambiguous", "details": "meeting reference unclear"},
    253: {"reason": "ambiguous", "details": "presence detection ambiguous"},
    255: {"reason": "ambiguous", "details": "which documents folder?"},
    256: {"reason": "ambiguous", "details": "search docs: unclear scope"},
    258: {"reason": "ambiguous", "details": "doc creation unclear"},
    261: {"reason": "ambiguous", "details": "email search missing parameters"},
    262: {"reason": "ambiguous", "details": "open ai roadmap unclear"},
    264: {"reason": "ambiguous", "details": "append target missing"},
    265: {"reason": "ambiguous", "details": "storage query unclear"},
    267: {"reason": "ambiguous", "details": "folder search unclear"},
    269: {"reason": "ambiguous", "details": "new doc target unclear"},
    271: {"reason": "ambiguous", "details": "spam folder deletion unsafe"},
    272: {"reason": "ambiguous", "details": "presence direction ambiguous"},
}

CANONICAL_MAPPING: Dict[int, Dict[str, str]] = {
    300: {"canonical_domain": "calendar", "canonical_action": "add_event"},
    301: {"canonical_domain": "reminder", "canonical_action": "create_reminder"},
    302: {"canonical_domain": "email", "canonical_action": "forward_email"},
    303: {"canonical_domain": "email_search", "canonical_action": "list_unread"},
    304: {"canonical_domain": "calendar", "canonical_action": "reschedule_event"},
    305: {"canonical_domain": "clarify", "canonical_action": "ask_clarification"},
    306: {"canonical_domain": "web_search", "canonical_action": "search"},
    307: {"canonical_domain": "vision", "canonical_action": "capture_image"},
    308: {"canonical_domain": "vision", "canonical_action": "detect_presence"},
    309: {"canonical_domain": "notes", "canonical_action": "save_note"},
    310: {"canonical_domain": "memory", "canonical_action": "retrieve"},
    311: {"canonical_domain": "memory", "canonical_action": "delete"},
    312: {"canonical_domain": "docs", "canonical_action": "find_duplicate"},
    313: {"canonical_domain": "files", "canonical_action": "rename"},
    314: {"canonical_domain": "docs", "canonical_action": "open_recent"},
    315: {"canonical_domain": "system", "canonical_action": "mode_toggle"},
    316: {"canonical_domain": "system", "canonical_action": "mode_toggle"},
    317: {"canonical_domain": "files", "canonical_action": "list"},
    318: {"canonical_domain": "system", "canonical_action": "set_volume"},
    319: {"canonical_domain": "docs", "canonical_action": "search"},
    320: {"canonical_domain": "email_search", "canonical_action": "search"},
    321: {"canonical_domain": "email", "canonical_action": "reply"},
    322: {"canonical_domain": "email", "canonical_action": "mark_unread"},
    323: {"canonical_domain": "email", "canonical_action": "delete_last"},
    324: {"canonical_domain": "calendar", "canonical_action": "list_events"},
    325: {"canonical_domain": "reminder", "canonical_action": "create_reminder"},
    326: {"canonical_domain": "robotics", "canonical_action": "movement_complex"},
    327: {"canonical_domain": "robotics", "canonical_action": "stop"},
    328: {"canonical_domain": "robotics", "canonical_action": "movement"},
    329: {"canonical_domain": "vision", "canonical_action": "capture_image"},
    330: {"canonical_domain": "system", "canonical_action": "disk_usage"},
    331: {"canonical_domain": "system", "canonical_action": "reboot"},
    332: {"canonical_domain": "system", "canonical_action": "shutdown"},
    333: {"canonical_domain": "calendar", "canonical_action": "reschedule_event"},
    334: {"canonical_domain": "calendar", "canonical_action": "reschedule_event"},
    335: {"canonical_domain": "clarify", "canonical_action": "ask_clarification"},
    336: {"canonical_domain": "reminder", "canonical_action": "search"},
    337: {"canonical_domain": "calendar", "canonical_action": "list_events"},
    338: {"canonical_domain": "docs", "canonical_action": "add_note"},
    339: {"canonical_domain": "docs", "canonical_action": "append"},
    340: {"canonical_domain": "docs", "canonical_action": "open"},
    341: {"canonical_domain": "files", "canonical_action": "duplicate"},
    342: {"canonical_domain": "docs", "canonical_action": "search_phrase"},
    343: {"canonical_domain": "docs", "canonical_action": "search"},
    344: {"canonical_domain": "docs", "canonical_action": "create"},
    345: {"canonical_domain": "docs", "canonical_action": "create"},
    346: {"canonical_domain": "docs", "canonical_action": "edit_section"},
    347: {"canonical_domain": "web_search", "canonical_action": "news"},
    348: {"canonical_domain": "web_search", "canonical_action": "image_search"},
    349: {"canonical_domain": "vision", "canonical_action": "detect_presence"},
    350: {"canonical_domain": "vision", "canonical_action": "detect_presence"},
    351: {"canonical_domain": "vision", "canonical_action": "capture_image"},
    352: {"canonical_domain": "memory", "canonical_action": "retrieve"},
    353: {"canonical_domain": "notes", "canonical_action": "save_note"},
    354: {"canonical_domain": "memory", "canonical_action": "delete"},
    355: {"canonical_domain": "memory", "canonical_action": "update"},
    356: {"canonical_domain": "web_search", "canonical_action": "search"},
    357: {"canonical_domain": "web_search", "canonical_action": "compare"},
    358: {"canonical_domain": "web_search", "canonical_action": "news"},
    359: {"canonical_domain": "email_search", "canonical_action": "list_unread"},
    360: {"canonical_domain": "email", "canonical_action": "forward"},
    361: {"canonical_domain": "email", "canonical_action": "reply"},
    362: {"canonical_domain": "email", "canonical_action": "mark_read"},
    363: {"canonical_domain": "email", "canonical_action": "delete_spam"},
    364: {"canonical_domain": "docs", "canonical_action": "open"},
    365: {"canonical_domain": "files", "canonical_action": "rename"},
    366: {"canonical_domain": "docs", "canonical_action": "add_note"},
    367: {"canonical_domain": "calendar", "canonical_action": "search_event"},
    368: {"canonical_domain": "calendar", "canonical_action": "list_events"},
    369: {"canonical_domain": "calendar", "canonical_action": "list_events"},
    370: {"canonical_domain": "reminder", "canonical_action": "create_reminder"},
    371: {"canonical_domain": "reminder", "canonical_action": "create_reminder"},
    372: {"canonical_domain": "reminder", "canonical_action": "create_reminder"},
    373: {"canonical_domain": "calendar", "canonical_action": "reschedule_event"},
    374: {"canonical_domain": "clarify", "canonical_action": "ask_clarification"},
    375: {"canonical_domain": "calendar", "canonical_action": "add_event"},
    376: {"canonical_domain": "docs", "canonical_action": "search_folder"},
    377: {"canonical_domain": "files", "canonical_action": "list"},
    378: {"canonical_domain": "docs", "canonical_action": "open"},
    379: {"canonical_domain": "docs", "canonical_action": "duplicate"},
    380: {"canonical_domain": "docs", "canonical_action": "append"},
    381: {"canonical_domain": "docs", "canonical_action": "create"},
    382: {"canonical_domain": "system", "canonical_action": "set_volume"},
    383: {"canonical_domain": "system", "canonical_action": "set_volume"},
    384: {"canonical_domain": "system", "canonical_action": "status"},
    385: {"canonical_domain": "system", "canonical_action": "disk_usage"},
    386: {"canonical_domain": "system", "canonical_action": "shutdown"},
    387: {"canonical_domain": "system", "canonical_action": "reboot"},
    388: {"canonical_domain": "system", "canonical_action": "stop_conversation"},
    389: {"canonical_domain": "system", "canonical_action": "switch_feature"},
    390: {"canonical_domain": "system", "canonical_action": "disable_mode"},
    391: {"canonical_domain": "system", "canonical_action": "enable_mode"},
    392: {"canonical_domain": "robotics", "canonical_action": "movement_complex"},
    393: {"canonical_domain": "robotics", "canonical_action": "movement"},
    394: {"canonical_domain": "robotics", "canonical_action": "idle"},
    395: {"canonical_domain": "vision", "canonical_action": "detect_presence"},
    396: {"canonical_domain": "vision", "canonical_action": "detect_presence"},
    397: {"canonical_domain": "vision", "canonical_action": "capture_image"},
    398: {"canonical_domain": "vision", "canonical_action": "capture_image"},
    399: {"canonical_domain": "vision", "canonical_action": "capture_image"},
    400: {"canonical_domain": "email_search", "canonical_action": "search_email"},
    401: {"canonical_domain": "email_search", "canonical_action": "search_email"},
    402: {"canonical_domain": "email", "canonical_action": "delete"},
    403: {"canonical_domain": "docs", "canonical_action": "open"},
    404: {"canonical_domain": "docs", "canonical_action": "create"},
    405: {"canonical_domain": "docs", "canonical_action": "create"},
    406: {"canonical_domain": "docs", "canonical_action": "rename"},
    407: {"canonical_domain": "docs", "canonical_action": "delete"},
    408: {"canonical_domain": "docs", "canonical_action": "list_recent"},
    409: {"canonical_domain": "docs", "canonical_action": "search_by_phrase"},
    410: {"canonical_domain": "docs", "canonical_action": "search_by_phrase"},
    411: {"canonical_domain": "docs", "canonical_action": "edit_section"},
    412: {"canonical_domain": "docs", "canonical_action": "append_note"},
    413: {"canonical_domain": "docs", "canonical_action": "append"},
    414: {"canonical_domain": "calendar", "canonical_action": "search_event"},
    415: {"canonical_domain": "calendar", "canonical_action": "move_event"},
    416: {"canonical_domain": "calendar", "canonical_action": "delete_event"},
    417: {"canonical_domain": "reminder", "canonical_action": "list"},
    418: {"canonical_domain": "reminder", "canonical_action": "create_reminder"},
    419: {"canonical_domain": "reminder", "canonical_action": "create_reminder"},
    420: {"canonical_domain": "reminder", "canonical_action": "create_reminder"},
    421: {"canonical_domain": "memory", "canonical_action": "update"},
    422: {"canonical_domain": "memory", "canonical_action": "save"},
    423: {"canonical_domain": "memory", "canonical_action": "delete"},
    424: {"canonical_domain": "memory", "canonical_action": "retrieve"},
    425: {"canonical_domain": "notes", "canonical_action": "save_note"},
    426: {"canonical_domain": "docs", "canonical_action": "open"},
    427: {"canonical_domain": "docs", "canonical_action": "open"},
    428: {"canonical_domain": "email", "canonical_action": "forward"},
    429: {"canonical_domain": "email", "canonical_action": "mark_spam"},
    430: {"canonical_domain": "email", "canonical_action": "mark_read"},
    431: {"canonical_domain": "email", "canonical_action": "forward"},
    432: {"canonical_domain": "web_search", "canonical_action": "search"},
    433: {"canonical_domain": "web_search", "canonical_action": "news"},
    434: {"canonical_domain": "web_search", "canonical_action": "image_search"},
    435: {"canonical_domain": "web_search", "canonical_action": "compare"},
    436: {"canonical_domain": "system", "canonical_action": "set_volume"},
    437: {"canonical_domain": "files", "canonical_action": "list"},
    438: {"canonical_domain": "docs", "canonical_action": "duplicate"},
    439: {"canonical_domain": "docs", "canonical_action": "append"},
    440: {"canonical_domain": "files", "canonical_action": "rename"},
    441: {"canonical_domain": "reminder", "canonical_action": "delete_reminder"},
    442: {"canonical_domain": "reminder", "canonical_action": "get_reminder"},
    443: {"canonical_domain": "calendar", "canonical_action": "get_events_today"},
    444: {"canonical_domain": "calendar", "canonical_action": "reschedule_appointment"},
    445: {"canonical_domain": "calendar", "canonical_action": "create_reminder"},
    446: {"canonical_domain": "docs", "canonical_action": "search_by_phrase"},
    447: {"canonical_domain": "docs", "canonical_action": "open"},
    448: {"canonical_domain": "docs", "canonical_action": "create"},
    449: {"canonical_domain": "docs", "canonical_action": "edit_section"},
    450: {"canonical_domain": "vision", "canonical_action": "capture_image"},
}

# Helper to check clarify
def should_clarify(query_id: int) -> bool:
    return query_id in CLARIFY_MAP
# --- CYCLE 3 UPDATE BEGIN ---

# Extend DOMAIN_MAP with new aliases detected in dataset
DOMAIN_MAP.update({
    "document_editing": "docs",
    "document_storage": "docs",
    "doc_search": "docs",
    "doc_creation": "docs",
    "email_search": "email",
    "email_management": "email",
    "audio_control": "system",
    "filesystem": "system",
    "file_system": "system",
})

# EMAIL canonical actions
ACTION_MAP.setdefault("email", {})
ACTION_MAP["email"].update({
    "search_inbox": "search_inbox",
    "search_email": "search_inbox",
    "search_new_email": "search_inbox",
    "search_unread_email": "search_unread_email",
    "get_last_email": "get_last_email",
    "forward_email": "forward_email",
    "reply_email": "reply_email",
    "delete_last_email": "delete_last_email",
    "mark_read": "mark_read",
    "mark_unread": "mark_unread",
})

# DOCS canonical actions
ACTION_MAP.setdefault("docs", {})
ACTION_MAP["docs"].update({
    "open_last_edited_document": "open_last_document",
    "rename_document": "rename_document",
    "duplicate_file": "duplicate_document",
    "duplicate_document": "duplicate_document",
    "list_documents": "list_documents",
    "open_document": "open_document",
    "append_document": "append_document",
    "add_milestone": "update_document",
    "append_note_to_project_plan": "append_document",
})

# CALENDAR canonical actions
ACTION_MAP.setdefault("calendar", {})
ACTION_MAP["calendar"].update({
    "get_upcoming_events": "list_events",
    "update_meeting": "move_event",
})

# TASKS canonical actions
ACTION_MAP.setdefault("tasks", {})
ACTION_MAP["tasks"].update({
    "set_reminder": "create_reminder",
    "cancel_reminder": "delete_reminder",
})

# MEMORY canonical actions
ACTION_MAP.setdefault("memory", {})
ACTION_MAP["memory"].update({
    "forget_data": "delete_memory",
})

# ROBOTICS canonical mapping
ACTION_MAP.setdefault("robotics", {})
ACTION_MAP["robotics"].update({
    "stop_robot": "stop",
    "perform_gesture": "run_routine",
})

# VISION canonical mapping
ACTION_MAP.setdefault("vision", {})
ACTION_MAP["vision"].update({
    "capture_image": "capture_snapshot",
    "detect_object_position": "capture_snapshot",
})

# SYSTEM canonical mappings
ACTION_MAP.setdefault("system", {})
ACTION_MAP["system"].update({
    "get_free_space": "get_disk_usage",
    "restart_process": "reboot",
    "set_volume": "set_volume",
})

# CLARIFY CASES
CLARIFY_MAP.update({
    101: {"reason": "multi_intent", "details": "sending email from jamie to richard ambiguous"},
    121: {"reason": "ambiguous", "details": "presence detection but domain unclear"},
    138: {"reason": "ambiguous", "details": "update section in doc vs plan-level action"},
    142: {"reason": "ambiguous", "details": "calendar summary vs list"},
    155: {"reason": "ambiguous", "details": "folder vs file/document search"},
    159: {"reason": "ambiguous", "details": "replying to which Jamie email?"},
})

# --- CYCLE 3 UPDATE END ---

# --- CYCLE 4 UPDATE BEGIN ---

# 1. DOMAIN ALIASES (normalize all new natural domains)
DOMAIN_MAP.update({
    "document_management": "docs",
    "doc_search": "docs",
    "doc_editing": "docs",
    "email_system": "email",
    "email_management": "email",
    "email_response": "email",
    "task_management": "tasks",
    "audio_control": "system",
    "audio": "system",
    "presence_detection": "vision",
    "browser_settings": "system",
    "tech": "search",
})

# 2. DOCS canonical mappings
ACTION_MAP["docs"].update({
    "open_document": "open_document",
    "delete_document": "delete_document",
    "search_documents": "search_documents",
    "search_docx_by_phrase": "search_documents",
    "update_document_section": "update_document",
})

# 3. EMAIL canonical mappings
ACTION_MAP.setdefault("email", {})
ACTION_MAP["email"].update({
    "forward_email": "forward_email",
    "mark_as_read": "mark_read",
    "delete_unread_messages": "delete_email",
    "list_unread_email": "search_unread_email",
})

# 4. CALENDAR canonical mappings
ACTION_MAP["calendar"].update({
    "get_events_by_date_range": "list_events",
    "reschedule_event": "move_event",
    "get_schedule": "list_events",
})

# 5. TASKS canonical mappings
ACTION_MAP["tasks"].update({
    "create_note": "store_note",
})

# 6. MEMORY canonical mappings
ACTION_MAP["memory"].update({
    "update_memory_note": "update_memory",
    "recall_project_details": "query_memories",
    "forget": "delete_memory",
    "retrieve_memory": "query_memories",
})

# 7. ROBOTICS canonical mappings
ACTION_MAP.setdefault("robotics", {})
ACTION_MAP["robotics"].update({
    "spin_robot": "run_routine",
})

# 8. VISION canonical mappings
ACTION_MAP.setdefault("vision", {})
ACTION_MAP["vision"].update({
    "take_photo": "capture_snapshot",
    "get_current_presence": "capture_snapshot",
})

# 9. SYSTEM canonical mappings
ACTION_MAP["system"].update({
    "get_available_memory": "get_system_status",
    "stop_conversation": "stop",
    "disable_bork_mode": "set_bork_mode_off",
})

# 10. SEARCH canonical mappings
ACTION_MAP.setdefault("search", {})
ACTION_MAP["search"].update({
    "compare_gpu_recommendation": "web_search",
    "search_for_news": "news_search",
})

# 11. CLARIFY CASES for ambiguous or unsafe intents
CLARIFY_MAP.update({
    202: {"reason": "ambiguous", "details": "dentist appointment requires calendar lookup"},
    203: {"reason": "ambiguous", "details": "time unclear to normalizer"},
    210: {"reason": "ambiguous", "details": "rename document unclear which file"},
    221: {"reason": "ambiguous", "details": "document selection unclear"},
    222: {"reason": "ambiguous", "details": "high-risk plan modification ambiguous"},
    224: {"reason": "ambiguous", "details": "meeting search needs structured event reference"},
    235: {"reason": "ambiguous", "details": "disk space query could be system or file domain"},
    237: {"reason": "ambiguous", "details": "doc creation context missing"},
    238: {"reason": "ambiguous", "details": "document reference unclear"},
    240: {"reason": "ambiguous", "details": "news search phrasing incomplete"},
    241: {"reason": "ambiguous", "details": "image search but source unclear"},
    244: {"reason": "ambiguous", "details": "reminder query lacks scope"},
    245: {"reason": "ambiguous", "details": "delete reminder without reference"},
    247: {"reason": "ambiguous", "details": "open which roadmap file?"},
    248: {"reason": "ambiguous", "details": "duplicate which document?"},
    249: {"reason": "ambiguous", "details": "append to which document?"},
    250: {"reason": "ambiguous", "details": "meeting reference unclear"},
    253: {"reason": "ambiguous", "details": "presence detection context unclear"},
    255: {"reason": "ambiguous", "details": "folder vs file listing unclear"},
    256: {"reason": "ambiguous", "details": "search scope unclear (folder/doc)"},
    258: {"reason": "ambiguous", "details": "create document but no clear title"},
    261: {"reason": "ambiguous", "details": "search email but parameters incomplete"},
    262: {"reason": "ambiguous", "details": "open doc but no clear canonical action"},
    264: {"reason": "ambiguous", "details": "append target unspecified"},
    265: {"reason": "ambiguous", "details": "storage measurement type not clear"},
    267: {"reason": "ambiguous", "details": "folder search unclear"},
    269: {"reason": "ambiguous", "details": "new doc but unclear context"},
    271: {"reason": "ambiguous", "details": "delete email from 'spam folder' ambiguous"},
    272: {"reason": "ambiguous", "details": "presence detection direction ambiguous"},
})

# --- CYCLE 4 UPDATE END ---


def map_natural_to_canonical(
    natural_domain: Optional[str],
    natural_action: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Map LLM's natural (domain, action) to canonical (domain, action).

    Returns (None, None) if either domain or action cannot be mapped.
    """
    if not natural_domain or not natural_action:
        return None, None

    dom = (natural_domain or "").strip().lower()
    act = (natural_action or "").strip()

    # Special-case: calendar+remind is really a tasks reminder.
    if dom == "calendar" and act.lower() == "remind":
        return "tasks", "create_reminder"

    canonical_domain = DOMAIN_MAP.get(dom)
    if not canonical_domain:
        return None, None

    domain_actions = ACTION_MAP.get(canonical_domain, {})
    canonical_action = domain_actions.get(act)
    if not canonical_action:
        return None, None

    return canonical_domain, canonical_action
