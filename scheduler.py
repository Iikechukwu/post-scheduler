"""
scheduler.py
------------
PostScheduler class — manages the queue of pending posts,
checks for due items, and triggers publishing.
Demonstrates: class with encapsulated state, method design, error handling.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Tuple

from models import Post, Platform
from api_clients import (
    ClientFactory,
    APIError,
    AuthenticationError,
    RateLimitError,
    NetworkError,
)


class SchedulerError(Exception):
    """Raised for scheduler-level problems (e.g. duplicate post, bad ID)."""


class PostScheduler:
    """
    Manages a queue of Post objects and coordinates publishing.

    Responsibilities
    ----------------
    - Add / remove posts from the queue.
    - Detect posts whose scheduled_time has arrived.
    - Delegate actual publishing to the appropriate API client.
    - Return structured results so the UI can show success / failure.
    """

    def __init__(self) -> None:
        # Internal queue: dict keyed by post.id for O(1) lookup
        self._queue: dict[str, Post] = {}

    # ── Queue management ──────────────────────────────────────────────────

    def schedule_post(self, post: Post) -> None:
        """
        Add a Post to the scheduler queue.

        Raises
        ------
        SchedulerError  if a post with the same ID already exists.
        TypeError       if post is not a Post instance.
        """
        if not isinstance(post, Post):
            raise TypeError(f"Expected Post, got {type(post).__name__}.")
        if post.id in self._queue:
            raise SchedulerError(f"Post '{post.id}' is already in the queue.")
        self._queue[post.id] = post

    def remove_post(self, post_id: str) -> Post:
        """
        Remove and return a post from the queue by ID.

        Raises
        ------
        SchedulerError if the post_id is not found.
        """
        if post_id not in self._queue:
            raise SchedulerError(f"No queued post with ID '{post_id}'.")
        return self._queue.pop(post_id)

    def get_scheduled_posts(self) -> List[Post]:
        """Return all posts currently in the queue (any status)."""
        return list(self._queue.values())

    def get_post_by_id(self, post_id: str) -> Post:
        """
        Retrieve a post from the queue without removing it.

        Raises
        ------
        SchedulerError if not found.
        """
        try:
            return self._queue[post_id]
        except KeyError:
            raise SchedulerError(f"Post '{post_id}' not found in queue.")

    def update_post(self, post_id: str, **updates) -> Post:
        """
        Update fields on a queued post.

        Supported fields: content, scheduled_time, status.
        Returns the updated Post.
        """
        post = self.get_post_by_id(post_id)
        allowed = {"content", "scheduled_time", "status"}
        unknown = set(updates) - allowed
        if unknown:
            raise SchedulerError(f"Unknown field(s) to update: {unknown}.")
        for field, value in updates.items():
            setattr(post, field, value)
        return post

    # ── Due-post detection ─────────────────────────────────────────────────

    def check_due_posts(self) -> List[Post]:
        """
        Return posts whose scheduled_time <= now and are still SCHEDULED.
        Does NOT publish — only identifies candidates.
        """
        now = datetime.now()
        return [
            post for post in self._queue.values()
            if post.status == "SCHEDULED" and post.scheduled_time <= now
        ]

    # ── Publishing ─────────────────────────────────────────────────────────

    def publish_now(self, post: Post, credentials: dict) -> str:
        """
        Immediately publish a single post via its platform's API client.

        Parameters
        ----------
        post        : The Post object to publish.
        credentials : dict with keys api_key, api_key_secret,
                      access_token, access_token_secret.

        Returns
        -------
        Confirmation string (tweet URL) on success.

        Raises
        ------
        AuthenticationError  – bad / missing credentials.
        RateLimitError       – platform rate limit hit.
        APIError             – other API-level failure.
        NetworkError         – connectivity problem.
        """
        client = ClientFactory.create(post.platform, credentials)
        confirmation = client.publish(post)
        post.mark_published()
        return confirmation

    def publish_due_posts(
        self,
        credentials: dict,
    ) -> Tuple[List[Post], List[Tuple[Post, str]]]:
        """
        Publish all due posts, collecting successes and failures.

        Parameters
        ----------
        credentials : dict with Twitter OAuth 1.0a keys.

        Returns
        -------
        (published_posts, failed_pairs)
        failed_pairs is a list of (Post, error_message) tuples.
        """
        due         = self.check_due_posts()
        published:  List[Post]               = []
        failed:     List[Tuple[Post, str]]   = []

        for post in due:
            try:
                confirmation = self.publish_now(post, credentials)
                self.remove_post(post.id)
                published.append(post)
                print(f"[PostScheduler] Published {post.id[:8]}: {confirmation}")

            except AuthenticationError as e:
                post.mark_failed(str(e))
                failed.append((post, f"Auth error: {e.message}"))

            except RateLimitError as e:
                post.mark_failed(str(e))
                failed.append((post, f"Rate limit: {e.message}"))

            except (APIError, NetworkError) as e:
                post.mark_failed(str(e))
                failed.append((post, str(e)))

            except Exception as e:
                post.mark_failed(str(e))
                failed.append((post, f"Unexpected: {e}"))

        return published, failed

    # ── Dunder methods ─────────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._queue)

    def __repr__(self) -> str:
        return f"PostScheduler(queued={len(self._queue)})"
