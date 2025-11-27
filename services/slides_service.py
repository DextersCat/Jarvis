import logging
from typing import Any, Dict, Optional

from services import google_helper

logger = logging.getLogger(__name__)


def create_presentation(title: str) -> Dict[str, Any]:
    slides = google_helper.build_service("slides")
    try:
        pres = slides.presentations().create(body={"title": title}).execute()
        pres_id = pres.get("presentationId")
        logger.info("[SlidesCreate] Created presentation id=%s title=%s", pres_id, title)
        return {
            "success": True,
            "action": "create_presentation",
            "details": {"id": pres_id, "title": title},
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("[SlidesCreate] Failed to create presentation: %s", exc)
        return {"success": False, "action": "create_presentation", "details": {"title": title, "error": str(exc)}}


def add_title_slide(presentation_id: str, title: str, subtitle: Optional[str] = None) -> Dict[str, Any]:
    slides = google_helper.build_service("slides")
    requests = [
        {
            "createSlide": {
                "slideLayoutReference": {"predefinedLayout": "TITLE_AND_SUBTITLE"},
            }
        },
        {
            "insertText": {
                "objectId": None,
                "insertionIndex": 0,
                "text": title,
            }
        },
    ]
    try:
        # Create slide first
        create_resp = slides.presentations().batchUpdate(
            presentationId=presentation_id, body={"requests": [requests[0]]}
        ).execute()
        slide_id = create_resp.get("replies", [{}])[0].get("createSlide", {}).get("objectId")
        insert_requests = []
        if title:
            insert_requests.append(
                {
                    "insertText": {
                        "objectId": slide_id,
                        "insertionIndex": 0,
                        "text": title,
                    }
                }
            )
        if subtitle:
            insert_requests.append(
                {
                    "insertText": {
                        "objectId": slide_id,
                        "insertionIndex": 0,
                        "text": "\n" + subtitle,
                    }
                }
            )
        if insert_requests:
            slides.presentations().batchUpdate(
                presentationId=presentation_id, body={"requests": insert_requests}
            ).execute()
        logger.info("[SlidesTitle] Added title slide to presentation id=%s", presentation_id)
        return {
            "success": True,
            "action": "add_title_slide",
            "details": {"presentation_id": presentation_id, "slide_id": slide_id, "title": title, "subtitle": subtitle},
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("[SlidesTitle] Failed to add title slide: %s", exc)
        return {
            "success": False,
            "action": "add_title_slide",
            "details": {"presentation_id": presentation_id, "error": str(exc)},
        }
