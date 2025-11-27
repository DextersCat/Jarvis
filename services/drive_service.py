import logging
from typing import Any, Dict, Optional

from services import google_helper

logger = logging.getLogger(__name__)


def find_file(name: str, mime_type: Optional[str] = None, max_results: int = 10) -> Dict[str, Any]:
    drive = google_helper.build_service("drive")
    query_parts = [f"name = '{name}'"]
    if mime_type:
        query_parts.append(f"mimeType = '{mime_type}'")
    query = " and ".join(query_parts)
    try:
        resp = (
            drive.files()
            .list(q=query, pageSize=max_results, fields="files(id, name, mimeType, parents)")
            .execute()
        )
        files = resp.get("files", [])
        logger.info("[DriveFind] Found %d files matching name=%s mime=%s", len(files), name, mime_type)
        return {"success": True, "action": "find_file", "details": {"files": files}}
    except Exception as exc:  # noqa: BLE001
        logger.error("[DriveFind] Failed to find file: %s", exc)
        return {"success": False, "action": "find_file", "details": {"error": str(exc), "name": name, "mime": mime_type}}


def rename_file(file_id: str, new_name: str) -> Dict[str, Any]:
    drive = google_helper.build_service("drive")
    try:
        file = drive.files().update(fileId=file_id, body={"name": new_name}).execute()
        logger.info("[DriveRename] Renamed file id=%s to %s", file_id, new_name)
        return {"success": True, "action": "rename_file", "details": {"id": file_id, "name": file.get("name")}}
    except Exception as exc:  # noqa: BLE001
        logger.error("[DriveRename] Failed to rename file %s: %s", file_id, exc)
        return {"success": False, "action": "rename_file", "details": {"id": file_id, "error": str(exc)}}


def move_file(file_id: str, new_parent_id: str) -> Dict[str, Any]:
    drive = google_helper.build_service("drive")
    try:
        # Retrieve the existing parents to remove
        file = drive.files().get(fileId=file_id, fields="parents").execute()
        previous_parents = ",".join(file.get("parents", []))
        updated = (
            drive.files()
            .update(fileId=file_id, addParents=new_parent_id, removeParents=previous_parents, fields="id, parents")
            .execute()
        )
        logger.info("[DriveMove] Moved file id=%s to parent=%s", file_id, new_parent_id)
        return {
            "success": True,
            "action": "move_file",
            "details": {"id": file_id, "new_parent": new_parent_id, "previous_parents": previous_parents, "response": updated},
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("[DriveMove] Failed to move file %s: %s", file_id, exc)
        return {"success": False, "action": "move_file", "details": {"id": file_id, "error": str(exc)}}


def delete_file(file_id: str) -> Dict[str, Any]:
    drive = google_helper.build_service("drive")
    try:
        drive.files().delete(fileId=file_id).execute()
        logger.info("[DriveDelete] Deleted file id=%s", file_id)
        return {"success": True, "action": "delete_file", "details": {"id": file_id}}
    except Exception as exc:  # noqa: BLE001
        logger.error("[DriveDelete] Failed to delete file %s: %s", file_id, exc)
        return {"success": False, "action": "delete_file", "details": {"id": file_id, "error": str(exc)}}
