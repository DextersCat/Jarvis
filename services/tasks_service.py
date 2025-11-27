import logging
from datetime import datetime
from typing import Any, Dict, Optional

from services import google_helper

logger = logging.getLogger(__name__)


def _service():
    return google_helper.build_service("tasks")


def _default_tasklist(tasklist_id: Optional[str] = None) -> str:
    return tasklist_id or "@default"


def list_tasks(tasklist_id: Optional[str] = None) -> Dict[str, Any]:
    svc = _service()
    tl = _default_tasklist(tasklist_id)
    try:
        items = svc.tasks().list(tasklist=tl, maxResults=100).execute().get("items", [])
        logger.info("[TasksList] Retrieved %d tasks from %s", len(items), tl)
        return {"success": True, "action": "list_tasks", "details": {"tasklist": tl, "count": len(items), "items": items}}
    except Exception as exc:  # noqa: BLE001
        logger.error("[TasksList] Failed to list tasks: %s", exc)
        return {"success": False, "action": "list_tasks", "details": {"tasklist": tl, "error": str(exc)}}


def create_task(title: str, due: Optional[datetime] = None, notes: Optional[str] = None, tasklist_id: Optional[str] = None) -> Dict[str, Any]:
    svc = _service()
    tl = _default_tasklist(tasklist_id)
    body: Dict[str, Any] = {"title": title}
    if notes:
        body["notes"] = notes
    if due:
        if due.tzinfo is None:
            due = due.replace(tzinfo=datetime.now().astimezone().tzinfo)
        body["due"] = due.isoformat()
    try:
        task = svc.tasks().insert(tasklist=tl, body=body).execute()
        logger.info("[TasksCreate] Created task id=%s title=%s", task.get("id"), title)
        return {"success": True, "action": "create_task", "details": {"tasklist": tl, "task": task}}
    except Exception as exc:  # noqa: BLE001
        logger.error("[TasksCreate] Failed to create task: %s", exc)
        return {"success": False, "action": "create_task", "details": {"tasklist": tl, "error": str(exc)}}


def update_task(task_id: str, patch: Dict[str, Any], tasklist_id: Optional[str] = None) -> Dict[str, Any]:
    svc = _service()
    tl = _default_tasklist(tasklist_id)
    try:
        task = svc.tasks().patch(tasklist=tl, task=task_id, body=patch).execute()
        logger.info("[TasksUpdate] Updated task id=%s", task_id)
        return {"success": True, "action": "update_task", "details": {"tasklist": tl, "task": task}}
    except Exception as exc:  # noqa: BLE001
        logger.error("[TasksUpdate] Failed to update task %s: %s", task_id, exc)
        return {"success": False, "action": "update_task", "details": {"tasklist": tl, "id": task_id, "error": str(exc)}}


def complete_task(task_id: str, tasklist_id: Optional[str] = None) -> Dict[str, Any]:
    svc = _service()
    tl = _default_tasklist(tasklist_id)
    try:
        task = svc.tasks().get(tasklist=tl, task=task_id).execute()
        task["status"] = "completed"
        updated = svc.tasks().update(tasklist=tl, task=task_id, body=task).execute()
        logger.info("[TasksComplete] Completed task id=%s", task_id)
        return {"success": True, "action": "complete_task", "details": {"tasklist": tl, "task": updated}}
    except Exception as exc:  # noqa: BLE001
        logger.error("[TasksComplete] Failed to complete task %s: %s", task_id, exc)
        return {"success": False, "action": "complete_task", "details": {"tasklist": tl, "id": task_id, "error": str(exc)}}


def delete_task(task_id: str, tasklist_id: Optional[str] = None) -> Dict[str, Any]:
    svc = _service()
    tl = _default_tasklist(tasklist_id)
    try:
        svc.tasks().delete(tasklist=tl, task=task_id).execute()
        logger.info("[TasksDelete] Deleted task id=%s", task_id)
        return {"success": True, "action": "delete_task", "details": {"tasklist": tl, "id": task_id}}
    except Exception as exc:  # noqa: BLE001
        logger.error("[TasksDelete] Failed to delete task %s: %s", task_id, exc)
        return {"success": False, "action": "delete_task", "details": {"tasklist": tl, "id": task_id, "error": str(exc)}}
