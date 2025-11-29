import logging
from typing import Any, Dict, List, Optional

from googleapiclient.errors import HttpError

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


def fetch_document(doc_id: str) -> Dict[str, Any]:
    docs = google_helper.build_service("docs")
    try:
        document = docs.documents().get(documentId=doc_id, fields="documentId,title,body").execute()
        logger.info("[DocsFetch] Retrieved document id=%s", doc_id)
        return {"success": True, "document": document}
    except HttpError as exc:  # noqa: BLE001
        logger.error("[DocsFetch] Failed to fetch doc id=%s: %s", doc_id, exc)
        return {"success": False, "error": str(exc), "details": {"id": doc_id}}


def search_docs(query: str, max_results: int = 5) -> Dict[str, Any]:
    drive = google_helper.build_service("drive")
    safe_query = query.replace("'", "\\'")
    q = (
        f"name contains '{safe_query}' and "
        "mimeType = 'application/vnd.google-apps.document' and trashed = false"
    )
    try:
        response = (
            drive.files()
            .list(q=q, pageSize=max_results, fields="files(id,name,owners)")
            .execute()
        )
        files = response.get("files", [])
        logger.info("[DocsSearch] Found %d docs for query=%s", len(files), query)
        return {"success": True, "files": files}
    except HttpError as exc:  # noqa: BLE001
        logger.error("[DocsSearch] Google Drive search failed: %s", exc)
        return {"success": False, "error": str(exc)}


def render_document_text(document: Dict[str, Any]) -> str:
    body = document.get("body", {})
    content = body.get("content", [])
    lines = []
    for element in content:
        paragraph = element.get("paragraph")
        if not paragraph:
            continue
        for el in paragraph.get("elements", []):
            text_run = el.get("textRun")
            if not text_run:
                continue
            lines.append(text_run.get("content", ""))
    return "".join(lines).strip()
