import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

LIBRARY_ROOT = Path("/mnt/f/JARVIS_LIBRARY")
INDEX_PATH = LIBRARY_ROOT / "jarvis_library_index.json"


def _ensure_library_root():
    LIBRARY_ROOT.mkdir(parents=True, exist_ok=True)
    (LIBRARY_ROOT / "emails").mkdir(parents=True, exist_ok=True)
    (LIBRARY_ROOT / "docs").mkdir(parents=True, exist_ok=True)
    (LIBRARY_ROOT / "docs" / "calendar").mkdir(parents=True, exist_ok=True)
    (LIBRARY_ROOT / "images").mkdir(parents=True, exist_ok=True)
    (LIBRARY_ROOT / "config").mkdir(parents=True, exist_ok=True)


def _load_index() -> Dict[str, Any]:
    _ensure_library_root()
    if not INDEX_PATH.exists():
        return {"items": []}
    try:
        with INDEX_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("[JarvisLibrary] Failed to load index (%s); starting fresh", exc)
        return {"items": []}


def _save_index(data: Dict[str, Any]):
    _ensure_library_root()
    with INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_item(
    category: str,
    title: str,
    tags: Optional[List[str]],
    library_path: str,
    metadata: Dict[str, Any],
    archive_path: Optional[str] = None,
    date_key: Optional[str] = None,
    created_at: Optional[str] = None,
) -> str:
    data = _load_index()
    item_id = str(uuid.uuid4())
    timestamp = created_at or datetime.now().isoformat()
    entry = {
        "id": item_id,
        "category": category,
        "timestamp": timestamp,
        "date_key": date_key,
        "title": title,
        "tags": tags or [],
        "library_path": library_path,
        "archive_path": archive_path,
        "metadata": metadata or {},
    }
    data.setdefault("items", []).append(entry)
    _save_index(data)
    logger.info(
        "[JarvisLibrary] Added item id=%s category=%s title=%s date_key=%s path=%s",
        item_id,
        category,
        title,
        date_key,
        library_path,
    )
    return item_id


def upsert_item(
    category: str,
    title: str,
    tags: Optional[List[str]],
    library_path: str,
    metadata: Dict[str, Any],
    archive_path: Optional[str] = None,
    date_key: Optional[str] = None,
    created_at: Optional[str] = None,
) -> str:
    """
    Update an existing entry matching category+date_key+library_path, else add.
    """
    data = _load_index()
    items = data.get("items", [])
    target = None
    for itm in items:
        if (
            itm.get("category") == category
            and itm.get("library_path") == library_path
            and (date_key is None or itm.get("date_key") == date_key)
        ):
            target = itm
            break
    if target:
        target["title"] = title
        target["tags"] = tags or []
        target["archive_path"] = archive_path
        target["metadata"] = metadata or {}
        target["date_key"] = date_key
        if created_at:
            target["timestamp"] = created_at
        logger.info(
            "[JarvisLibrary] Updated item id=%s category=%s date_key=%s path=%s",
            target.get("id"),
            category,
            date_key,
            library_path,
        )
        _save_index(data)
        return target.get("id")
    return add_item(
        category=category,
        title=title,
        tags=tags,
        library_path=library_path,
        metadata=metadata,
        archive_path=archive_path,
        date_key=date_key,
        created_at=created_at,
    )


def _filter_items(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    date_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    data = _load_index()
    items = data.get("items", [])
    result = []
    for itm in items:
        if category and itm.get("category") != category:
            continue
        if tag and tag not in itm.get("tags", []):
            continue
        if date_key and itm.get("date_key") != date_key:
            continue
        ts = itm.get("timestamp")
        if since and ts and ts < since:
            continue
        if until and ts and ts > until:
            continue
        result.append(itm)
    return result


def get_latest(category: str, filter_tags: Optional[List[str]] = None, date_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    items = _filter_items(category=category, date_key=date_key)
    if filter_tags:
        items = [i for i in items if set(filter_tags).intersection(set(i.get("tags", [])))]
    if not items:
        return None
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return items[0]


def get_by_date(category: str, date_prefix: str, filter_tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    # date_prefix like "2025-11-22"
    items = _filter_items(category=category, date_key=date_prefix)
    if filter_tags:
        items = [i for i in items if set(filter_tags).intersection(set(i.get("tags", [])))]
    return items


def search(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    date_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    items = _filter_items(category=category, tag=tag, since=since, until=until, date_key=date_key)
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return items
