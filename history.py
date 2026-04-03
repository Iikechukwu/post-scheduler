"""
history.py
----------
PostHistory class — persistent JSON-backed log of all posts.
Demonstrates: file I/O, JSON serialisation, error handling, class design.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import List

from models import Post


class HistoryError(Exception):
    """Raised when the history file cannot be read or written."""


class PostHistory:
    """
    Persists a log of all Post activity to a local JSON file.

    Each record is a plain dict (not a full Post object) so the history
    survives across Streamlit sessions even after the Post objects are
    garbage-collected.

    Attributes
    ----------
    filepath : Path to the JSON file used for storage.
    """

    DEFAULT_PATH = "post_history.json"

    def __init__(self, filepath: str = DEFAULT_PATH) -> None:
        self.filepath = filepath
        self._records: List[dict] = self._load()

    # ── Private helpers ───────────────────────────────────────────────────

    def _load(self) -> List[dict]:
        """
        Load records from disk.
        Returns an empty list if the file doesn't exist yet.
        Raises HistoryError if the file exists but is corrupted.
        """
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise HistoryError(
                    f"History file '{self.filepath}' is malformed "
                    "(expected a JSON array)."
                )
            return data
        except json.JSONDecodeError as e:
            raise HistoryError(
                f"Could not parse history file '{self.filepath}': {e}"
            ) from e
        except OSError as e:
            raise HistoryError(
                f"Could not read history file '{self.filepath}': {e}"
            ) from e

    def _save(self) -> None:
        """
        Write current records to disk.
        Raises HistoryError on any OS-level failure.
        """
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self._records, f, indent=2, default=str)
        except OSError as e:
            raise HistoryError(
                f"Could not write history file '{self.filepath}': {e}"
            ) from e

    def _find_index(self, post_id: str) -> int:
        """
        Return the list index of the record with the given ID.
        Returns -1 if not found.
        """
        for i, record in enumerate(self._records):
            if record.get("id") == post_id:
                return i
        return -1

    # ── Public API ────────────────────────────────────────────────────────

    def add_post(self, post: Post) -> None:
        """
        Append a Post's serialised form to the history.
        Safe to call multiple times — won't add duplicates.
        """
        if not isinstance(post, Post):
            raise TypeError(f"Expected Post, got {type(post).__name__}.")
        if self._find_index(post.id) != -1:
            # Already recorded; just update status
            self.update_post_status(post.id, post.status)
            return
        self._records.append(post.to_dict())
        self._save()

    def update_post_status(self, post_id: str, new_status: str) -> None:
        """
        Update the status field of an existing history record.

        Raises
        ------
        KeyError if no record with that ID exists.
        """
        idx = self._find_index(post_id)
        if idx == -1:
            raise KeyError(f"No history record for post ID '{post_id}'.")
        self._records[idx]["status"] = new_status
        self._records[idx]["updated_at"] = datetime.now().isoformat()
        self._save()

    def get_all_posts(self) -> List[dict]:
        """Return a shallow copy of all history records."""
        return list(self._records)

    def get_posts_by_platform(self, platform: str) -> List[dict]:
        """Return records for a specific platform (e.g. 'twitter')."""
        return [r for r in self._records if r.get("platform") == platform.lower()]

    def get_posts_by_status(self, status: str) -> List[dict]:
        """Return records with a specific status (e.g. 'PUBLISHED')."""
        return [r for r in self._records if r.get("status") == status.upper()]

    def get_post_by_id(self, post_id: str) -> dict | None:
        """Return the record dict for a given ID, or None if not found."""
        idx = self._find_index(post_id)
        return self._records[idx] if idx != -1 else None

    def clear_history(self) -> None:
        """Delete all records from memory and from disk."""
        self._records.clear()
        self._save()

    def delete_post(self, post_id: str) -> None:
        """
        Remove a single record from history by ID.

        Raises
        ------
        KeyError if not found.
        """
        idx = self._find_index(post_id)
        if idx == -1:
            raise KeyError(f"No history record for post ID '{post_id}'.")
        del self._records[idx]
        self._save()

    # ── Stats helpers ──────────────────────────────────────────────────────

    def summary(self) -> dict:
        """Return a dict of aggregate counts."""
        total = len(self._records)
        by_status: dict[str, int] = {}
        by_platform: dict[str, int] = {}
        for r in self._records:
            s = r.get("status", "UNKNOWN")
            p = r.get("platform", "unknown")
            by_status[s]   = by_status.get(s, 0) + 1
            by_platform[p] = by_platform.get(p, 0) + 1
        return {
            "total":       total,
            "by_status":   by_status,
            "by_platform": by_platform,
        }

    # ── Dunder methods ─────────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._records)

    def __repr__(self) -> str:
        return f"PostHistory(filepath={self.filepath!r}, records={len(self._records)})"
