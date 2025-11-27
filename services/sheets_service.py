import logging
from typing import Any, Dict, List, Optional

from services import google_helper

logger = logging.getLogger(__name__)


def create_sheet(title: str, headers: Optional[List[str]] = None) -> Dict[str, Any]:
    sheets = google_helper.build_service("sheets")
    body = {"properties": {"title": title}}
    try:
        resp = sheets.spreadsheets().create(body=body).execute()
        spreadsheet_id = resp.get("spreadsheetId")
        logger.info("[SheetsCreate] Created spreadsheet id=%s title=%s", spreadsheet_id, title)
        if headers:
            sheets.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range="Sheet1!1:1",
                valueInputOption="RAW",
                body={"values": [headers]},
            ).execute()
        return {
            "success": True,
            "action": "create_sheet",
            "details": {"id": spreadsheet_id, "title": title, "headers": headers or []},
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("[SheetsCreate] Failed to create sheet: %s", exc)
        return {"success": False, "action": "create_sheet", "details": {"title": title, "error": str(exc)}}


def append_row(spreadsheet_id: str, range_a1: str, values: List[Any]) -> Dict[str, Any]:
    sheets = google_helper.build_service("sheets")
    try:
        resp = sheets.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_a1,
            valueInputOption="RAW",
            body={"values": [values]},
        ).execute()
        logger.info("[SheetsAppend] Appended row to %s range=%s", spreadsheet_id, range_a1)
        return {
            "success": True,
            "action": "append_row",
            "details": {"spreadsheet_id": spreadsheet_id, "range": range_a1, "values": values, "response": resp},
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("[SheetsAppend] Failed to append row: %s", exc)
        return {
            "success": False,
            "action": "append_row",
            "details": {"spreadsheet_id": spreadsheet_id, "range": range_a1, "error": str(exc)},
        }
