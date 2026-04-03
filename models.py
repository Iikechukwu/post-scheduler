"""
models.py
---------
Core data models for PostFlow.
Demonstrates: classes, enums, data encapsulation, __repr__, __str__.
"""

import uuid
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field


class Platform(Enum):
    """Enumeration of supported social media platforms."""
    TWITTER = "twitter"

    def __str__(self) -> str:
        return self.value.capitalize()

    @classmethod
    def from_string(cls, name: str) -> "Platform":
        """
        Factory method: create Platform from a string.
        Raises ValueError if unrecognised.
        """
        name = name.strip().lower()
        mapping = {
            "twitter": cls.TWITTER,
            "x":       cls.TWITTER,
        }
        if name not in mapping:
            raise ValueError(
                f"Unsupported platform '{name}'. "
                f"Choose from: {', '.join(mapping.keys())}"
            )
        return mapping[name]


@dataclass
class Post:
    """
    Represents a single social media post.

    Attributes
    ----------
    content        : The text body of the post.
    platform       : Which platform this post targets.
    scheduled_time : When the post should go live.
    status         : Lifecycle state (DRAFT, SCHEDULED, PUBLISHED, FAILED, CANCELLED).
    id             : Unique identifier (auto-generated UUID).
    created_at     : Timestamp of when this Post object was created.
    error_message  : Stores the last error string if publish fails.
    """
    content:        str
    platform:       Platform
    scheduled_time: datetime
    status:         str                    = "SCHEDULED"
    id:             str                    = field(default_factory=lambda: str(uuid.uuid4()))
    created_at:     datetime               = field(default_factory=datetime.now)
    error_message:  str | None             = None

    # ── Validation ─────────────────────────────────────────────────────────
    def __post_init__(self) -> None:
        """Validate fields immediately after dataclass creation."""
        if not isinstance(self.platform, Platform):
            raise TypeError(f"platform must be a Platform enum, got {type(self.platform)}")
        self._validate_content()
        self._validate_status()

    def _validate_content(self) -> None:
        limits = {
            Platform.TWITTER: 280,
        }
        limit = limits[self.platform]
        if not self.content or not self.content.strip():
            raise ValueError("Post content cannot be empty.")
        if len(self.content) > limit:
            raise ValueError(
                f"{self.platform} posts cannot exceed {limit} characters "
                f"(current: {len(self.content)})."
            )

    def _validate_status(self) -> None:
        valid = {"DRAFT", "SCHEDULED", "PUBLISHED", "FAILED", "CANCELLED", "PUBLISH_NOW"}
        if self.status not in valid:
            raise ValueError(f"Invalid status '{self.status}'. Must be one of {valid}.")

    # ── Helpers ────────────────────────────────────────────────────────────
    def is_due(self) -> bool:
        """Return True if the scheduled time is now or in the past."""
        return datetime.now() >= self.scheduled_time

    def mark_published(self) -> None:
        self.status = "PUBLISHED"

    def mark_failed(self, reason: str = "") -> None:
        self.status        = "FAILED"
        self.error_message = reason

    def to_dict(self) -> dict:
        """Serialise to a plain dict (for JSON persistence)."""
        return {
            "id":             self.id,
            "content":        self.content,
            "platform":       self.platform.value,
            "scheduled_time": self.scheduled_time.isoformat(),
            "status":         self.status,
            "created_at":     self.created_at.isoformat(),
            "error_message":  self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Post":
        """Deserialise from a plain dict (for JSON loading)."""
        return cls(
            id             = data["id"],
            content        = data["content"],
            platform       = Platform(data["platform"]),
            scheduled_time = datetime.fromisoformat(data["scheduled_time"]),
            status         = data.get("status", "SCHEDULED"),
            created_at     = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            error_message  = data.get("error_message"),
        )

    def __repr__(self) -> str:
        return (
            f"Post(id={self.id[:8]!r}, platform={self.platform.value!r}, "
            f"status={self.status!r}, scheduled={self.scheduled_time.isoformat()!r})"
        )

    def __str__(self) -> str:
        return (
            f"[{self.platform}] {self.status} · "
            f"{self.scheduled_time.strftime('%Y-%m-%d %H:%M')} · "
            f"{self.content[:60]}{'...' if len(self.content) > 60 else ''}"
        )
