"""
Jarvis File Service (Skeleton)

This module provides a single, safe entry point for all future Jarvis file I/O.
Current implementation is non-destructive: no directories are created and no
files are written. Methods are stubs or planning helpers only.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class JarvisFileService:
    """
    Stubbed file service for Jarvis Brain.

    All real file operations will be routed through this service in the future.
    For now, methods are non-destructive and primarily build plans or raise
    explicit NotImplemented errors.
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the service with an optional base vault path.

        Args:
            base_path: Optional base vault path (e.g., from JARVIS_VAULT_PATH).
                       If invalid or missing, the service remains disabled.
        """
        self.base_path: Optional[Path] = None

        if base_path:
            candidate = Path(base_path).expanduser()
            if candidate.is_dir():
                self.base_path = candidate
                logger.info(f"FileService initialised (stub) with base path: {candidate}")
            else:
                logger.warning(
                    f"FileService disabled: base path does not exist or is not a directory: {candidate}"
                )
        else:
            logger.info("FileService disabled: no base path provided (JARVIS_VAULT_PATH not set).")

    @property
    def is_enabled(self) -> bool:
        """Returns True if the service has a valid base path configured."""
        return self.base_path is not None and self.base_path.is_dir()

    def ensure_base_path(self) -> Dict[str, Any]:
        """
        Validate that the base vault path exists and is a directory.

        Non-destructive: does not create directories.
        Returns:
            Structured result with success flag and message.
        """
        if not self.base_path:
            msg = "FileService base path not configured; set JARVIS_VAULT_PATH."
            logger.warning(msg)
            return {"success": False, "message": msg}

        if not self.base_path.is_dir():
            msg = f"Configured base path missing or invalid: {self.base_path}"
            logger.warning(msg)
            return {"success": False, "message": msg}

        return {"success": True, "message": "Base path valid."}

    def build_dated_path(self, category: Optional[str] = None) -> str:
        """
        Construct a dated path under the base vault, optionally under a category.

        Example: <base>/2025/11/21/notes/
        Non-destructive: does not create directories.

        Args:
            category: Optional category subfolder (e.g., "notes", "projects").
        Returns:
            String path to the intended folder for today's date.
        """
        base_check = self.ensure_base_path()
        if not base_check.get("success"):
            raise ValueError(base_check.get("message", "Base path is not configured; cannot build dated path."))

        today = datetime.now()
        parts = [
            str(self.base_path),
            f"{today.year:04d}",
            f"{today.month:02d}",
            f"{today.day:02d}",
        ]

        if category:
            safe_category = self._sanitize_segment(category)
            parts.append(safe_category)

        return str(Path(*parts))

    def sanitize_filename(self, name: str, ext: str) -> str:
        """
        Return a safe filename from a human-friendly name and extension.

        Planned behaviour:
        - strip/replace illegal characters
        - normalise whitespace
        - enforce predictable, low-risk naming

        Current behaviour: simple sanitisation; no filesystem writes occur.
        """
        base = re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("_")
        base = base or "untitled"
        clean_ext = ext if ext.startswith(".") else f".{ext}"
        return f"{base}{clean_ext}"

    def plan_file_creation(
        self,
        name: str,
        ext: str,
        category: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        content_preview: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a plan describing where a file would be created, without touching disk.

        Returns:
            Dict with keys like: type, base_path, target_folder, filename,
            full_path, category, metadata, preview.
        """
        base_check = self.ensure_base_path()
        if not base_check.get("success"):
            return {
                "type": "plan",
                "status": "disabled",
                "reason": base_check.get("message", "Base path not configured or invalid."),
            }

        target_folder = self.build_dated_path(category)
        filename = self.sanitize_filename(name, ext)
        full_path = str(Path(target_folder) / filename)

        return {
            "type": "plan",
            "status": "ok",
            "base_path": str(self.base_path),
            "target_folder": target_folder,
            "filename": filename,
            "full_path": full_path,
            "category": category,
            "metadata": metadata or {},
            "preview": content_preview,
        }

    def create_file(
        self,
        name: str,
        ext: str,
        category: Optional[str] = None,
        content: str = "",
        allow_overwrite: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a text/markdown file under the dated vault path.

        Behaviour:
        - Validates base path.
        - Builds dated path (with optional category) and creates the folder tree.
        - Prevents silent overwrite; if a collision occurs, adds a timestamp suffix
          unless allow_overwrite is True.
        - Writes content and returns a structured result.
        """
        base_check = self.ensure_base_path()
        if not base_check.get("success"):
            return self._error_result(base_check.get("message"))

        try:
            target_dir = Path(self.build_dated_path(category))
            self._ensure_directory(target_dir)
        except Exception as exc:
            msg = f"Failed to prepare target directory: {exc}"
            logger.error(msg)
            return self._error_result(msg)

        filename = self.sanitize_filename(name, ext)
        target_path = target_dir / filename
        target_path = self._ensure_within_base(target_path)
        if not target_path:
            msg = "Refusing to write outside configured vault path."
            logger.error(msg)
            return self._error_result(msg)

        final_path = target_path
        if final_path.exists() and not allow_overwrite:
            timestamp = datetime.now().strftime("%H%M%S")
            final_path = target_path.with_name(f"{target_path.stem}_{timestamp}{target_path.suffix}")
            logger.info(f"File exists, using timestamped name: {final_path.name}")

        try:
            final_path.write_text(content, encoding="utf-8")
        except Exception as exc:
            msg = f"Failed to write file: {exc}"
            logger.error(msg)
            return self._error_result(msg, full_path=str(final_path))

        logger.info(f"File created: {final_path}")
        return {
            "success": True,
            "message": "File created.",
            "full_path": str(final_path),
            "filename": final_path.name,
            "category": category,
        }

    def append_to_file(
        self,
        name: str,
        ext: str,
        category: Optional[str] = None,
        content: str = "",
    ) -> Dict[str, Any]:
        """
        Append text with a newline to a log/notes file under the dated vault path.

        Behaviour:
        - Validates base path.
        - Ensures the dated folder exists (created if needed).
        - Creates the file if missing; otherwise appends.
        """
        base_check = self.ensure_base_path()
        if not base_check.get("success"):
            return self._error_result(base_check.get("message"))

        try:
            target_dir = Path(self.build_dated_path(category))
            self._ensure_directory(target_dir)
        except Exception as exc:
            msg = f"Failed to prepare target directory: {exc}"
            logger.error(msg)
            return self._error_result(msg)

        filename = self.sanitize_filename(name, ext)
        target_path = target_dir / filename
        target_path = self._ensure_within_base(target_path)
        if not target_path:
            msg = "Refusing to write outside configured vault path."
            logger.error(msg)
            return self._error_result(msg)

        try:
            with target_path.open("a", encoding="utf-8") as f:
                f.write(content)
                if not content.endswith("\n"):
                    f.write("\n")
        except Exception as exc:
            msg = f"Failed to append to file: {exc}"
            logger.error(msg)
            return self._error_result(msg, full_path=str(target_path))

        logger.info(f"Appended to file: {target_path}")
        return {
            "success": True,
            "message": "Content appended.",
            "full_path": str(target_path),
            "filename": target_path.name,
            "category": category,
        }

    def create_structured_log(self, *args, **kwargs):
        """
        Future behaviour:
        - Write structured JSON/YAML logs for system reports, checks, or summaries.
        - Include metadata and schema validation.

        Current behaviour: non-destructive stub.
        """
        raise NotImplementedError("JarvisFileService.create_structured_log is not implemented yet.")

    @staticmethod
    def _sanitize_segment(segment: str) -> str:
        """Sanitise a path segment without touching disk."""
        return re.sub(r"[^a-zA-Z0-9._-]+", "_", segment).strip("_") or "uncategorized"

    def _ensure_directory(self, path: Path) -> None:
        """
        Ensure a directory exists under the base path.

        Directory creation is allowed only under the configured base path.
        """
        safe_path = self._ensure_within_base(path)
        if not safe_path:
            raise ValueError("Refusing to create directory outside vault path.")
        safe_path.mkdir(parents=True, exist_ok=True)

    def _ensure_within_base(self, path: Path) -> Optional[Path]:
        """
        Return the path if it is within the configured base path; otherwise None.
        """
        if not self.base_path:
            return None
        try:
            if path.resolve().is_relative_to(self.base_path.resolve()):
                return path
        except Exception:
            # For Python versions lacking is_relative_to, fall back to manual check
            base_resolved = str(self.base_path.resolve())
            path_resolved = str(path.resolve())
            if path_resolved.startswith(base_resolved):
                return path
        return None

    @staticmethod
    def _error_result(message: str, full_path: Optional[str] = None) -> Dict[str, Any]:
        """Helper to return a structured error result."""
        result = {"success": False, "message": message}
        if full_path:
            result["full_path"] = full_path
        return result
