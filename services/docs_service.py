import logging
from typing import Any, Dict, Optional

from services import google_helper

logger = logging.getLogger(__name__)


def create_doc(title: str, initial_content: Optional[str] = None) -> Dict[str, Any]:
    docs = google_helper.build_service("docs")
    try:
        doc = docs.documents().create(body={"title": title}).execute()
        doc_id = doc.get("documentId")
        logger.info("[DocsCreate] Created doc id=%s title=%s", doc_id, title)
        if initial_content:
            requests = [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": initial_content,
                    }
                }
            ]
            docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
        return {
            "success": True,
            "action": "create_doc",
            "details": {"id": doc_id, "title": title, "initial_content": bool(initial_content)},
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("[DocsCreate] Failed to create doc: %s", exc)
        return {"success": False, "action": "create_doc", "details": {"title": title, "error": str(exc)}}


def append_to_doc(doc_id: str, content: str) -> Dict[str, Any]:
    docs = google_helper.build_service("docs")
    try:
        # Append at end: use location index equal to end of document (-1)
        requests = [
            {
                "insertText": {
                    "endOfSegmentLocation": {},
                    "text": content,
                }
            }
        ]
        docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
        logger.info("[DocsAppend] Appended content to doc id=%s", doc_id)
        return {"success": True, "action": "append_to_doc", "details": {"id": doc_id, "appended_len": len(content)}}
    except Exception as exc:  # noqa: BLE001
        logger.error("[DocsAppend] Failed to append to doc %s: %s", doc_id, exc)
        return {"success": False, "action": "append_to_doc", "details": {"id": doc_id, "error": str(exc)}}
