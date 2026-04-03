"""
api_clients.py
--------------
Twitter API v2 client for PostFlow.
Uses OAuth 1.0a User Context (API Key + Access Token) which is required
to post tweets on the free/Basic tier of the Twitter API.

Demonstrates: inheritance, abstract base class, polymorphism, exception handling.
"""

import time
import requests
from requests_oauthlib import OAuth1
from abc import ABC, abstractmethod
from models import Post, Platform


# ── Custom exceptions ─────────────────────────────────────────────────────────

class APIError(Exception):
    """Raised when an API call returns an error response."""
    def __init__(self, platform: str, status_code: int, message: str) -> None:
        self.platform    = platform
        self.status_code = status_code
        self.message     = message
        super().__init__(f"[{platform}] HTTP {status_code}: {message}")


class AuthenticationError(APIError):
    """Raised when API credentials are missing or invalid."""


class RateLimitError(APIError):
    """Raised when the API rate limit is exceeded."""


class NetworkError(Exception):
    """Raised for connection-level failures (no response from server)."""


# ── Abstract base class ───────────────────────────────────────────────────────

class SocialMediaClient(ABC):
    """
    Abstract base class for social media API clients.
    Enforces a common interface via abstract methods.
    """

    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds between retries

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Human-readable platform name."""

    @abstractmethod
    def _post_request(self, content: str) -> dict:
        """Make the actual HTTP call and return the parsed response dict."""

    def publish(self, post: Post) -> str:
        """
        Publish a post with automatic retry on transient failures.
        Returns a confirmation URL string on success.
        Raises APIError / NetworkError on unrecoverable failure.
        """
        last_error = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                result = self._post_request(post.content)
                return self._extract_confirmation(result)

            except RateLimitError:
                raise  # never retry rate-limit errors

            except AuthenticationError:
                raise  # never retry auth errors

            except (APIError, NetworkError) as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY * attempt)
                continue

        raise last_error

    def _extract_confirmation(self, response: dict) -> str:
        return str(response)

    def _handle_response(self, response: requests.Response) -> dict:
        """Centralised HTTP response handler — maps status codes to exceptions."""
        if response.status_code == 401:
            raise AuthenticationError(
                self.platform_name, 401,
                "Invalid credentials. Double-check all four keys in Settings."
            )
        if response.status_code == 403:
            raise AuthenticationError(
                self.platform_name, 403,
                "Forbidden. Make sure your app has 'Read and Write' permissions "
                "AND that you regenerated your Access Token after changing them."
            )
        if response.status_code == 429:
            reset = response.headers.get("x-rate-limit-reset", "unknown")
            raise RateLimitError(
                self.platform_name, 429,
                f"Rate limit exceeded. Resets at Unix time: {reset}"
            )
        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text[:200]
            raise APIError(self.platform_name, response.status_code, str(detail))

        try:
            return response.json()
        except ValueError as e:
            raise APIError(
                self.platform_name, response.status_code,
                f"Invalid JSON in response: {e}"
            ) from e


# ── Twitter / X client ────────────────────────────────────────────────────────

class TwitterClient(SocialMediaClient):
    """
    Twitter API v2 client — posts tweets via the /2/tweets endpoint.

    Uses OAuth 1.0a User Context, which is the authentication method
    required to write tweets on the free/Basic API tier.

    Required credentials (all four from the Developer Portal):
        api_key             – API Key (Consumer Key)
        api_key_secret      – API Key Secret (Consumer Secret)
        access_token        – Access Token
        access_token_secret – Access Token Secret

    Docs:
        https://developer.twitter.com/en/docs/twitter-api/tweets/manage-tweets/api-reference/post-tweets
    """

    API_URL = "https://api.twitter.com/2/tweets"

    def __init__(
        self,
        api_key: str,
        api_key_secret: str,
        access_token: str,
        access_token_secret: str,
    ) -> None:
        # Validate that all four credentials are present
        missing = [
            name for name, val in [
                ("API Key",              api_key),
                ("API Key Secret",       api_key_secret),
                ("Access Token",         access_token),
                ("Access Token Secret",  access_token_secret),
            ]
            if not val or not val.strip()
        ]
        if missing:
            raise AuthenticationError(
                "Twitter / X", 0,
                f"Missing credentials: {', '.join(missing)}. "
                "Please fill in all four fields in ⚙️ Settings."
            )

        self.api_key             = api_key.strip()
        self.api_key_secret      = api_key_secret.strip()
        self.access_token        = access_token.strip()
        self.access_token_secret = access_token_secret.strip()

        # Build the OAuth1 signer once — reused on every request
        self._auth = OAuth1(
            self.api_key,
            self.api_key_secret,
            self.access_token,
            self.access_token_secret,
        )

    @property
    def platform_name(self) -> str:
        return "Twitter / X"

    def _post_request(self, content: str) -> dict:
        try:
            response = requests.post(
                self.API_URL,
                json={"text": content},
                auth=self._auth,
                timeout=10,
            )
        except requests.ConnectionError as e:
            raise NetworkError(f"Could not connect to Twitter API: {e}") from e
        except requests.Timeout:
            raise NetworkError("Twitter API request timed out after 10 seconds.")

        return self._handle_response(response)

    def _extract_confirmation(self, response: dict) -> str:
        tweet_id = response.get("data", {}).get("id", "unknown")
        return f"https://twitter.com/i/web/status/{tweet_id}"


# ── Client factory ────────────────────────────────────────────────────────────

class ClientFactory:
    """
    Factory class that creates the appropriate API client.
    Currently supports Twitter / X only.
    Demonstrates the Factory design pattern.
    """

    @staticmethod
    def create(platform: Platform, credentials: dict) -> SocialMediaClient:
        """
        Build and return a SocialMediaClient for the given platform.

        Parameters
        ----------
        platform    : Platform enum value (only TWITTER supported)
        credentials : dict with keys:
                        api_key, api_key_secret,
                        access_token, access_token_secret

        Raises
        ------
        ValueError           – unsupported platform
        AuthenticationError  – missing credentials
        """
        if platform == Platform.TWITTER:
            return TwitterClient(
                api_key             = credentials.get("api_key", ""),
                api_key_secret      = credentials.get("api_key_secret", ""),
                access_token        = credentials.get("access_token", ""),
                access_token_secret = credentials.get("access_token_secret", ""),
            )
        else:
            raise ValueError(
                f"Unsupported platform: {platform}. "
                "PostFlow currently supports Twitter / X only."
            )
