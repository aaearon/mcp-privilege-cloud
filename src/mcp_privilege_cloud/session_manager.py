"""Per-user session lifecycle management.

Manages a cache of CyberArkMCPServer instances keyed by SHA-256 of the
user's access token. Handles session creation, TTL expiry, max_sessions
limits, and graceful shutdown.
"""

import hashlib
import logging
import time
from typing import Any, Dict, Optional

from .server import CyberArkMCPServer

logger = logging.getLogger(__name__)


class UserSessionManager:
    """Manage per-user CyberArkMCPServer sessions.

    Each user's Bearer token maps to an isolated server instance via
    CyberArkMCPServer.from_token(). Sessions are cached by SHA-256
    of the token and evicted after TTL expiry or when max_sessions
    is exceeded.
    """

    def __init__(
        self,
        max_sessions: int = 100,
        session_ttl: int = 3600,
    ) -> None:
        """Initialize the session manager.

        Args:
            max_sessions: Maximum number of concurrent user sessions.
            session_ttl: Session time-to-live in seconds.
        """
        self._max_sessions = max_sessions
        self._session_ttl = session_ttl
        self._sessions: Dict[str, Dict[str, Any]] = {}

        logger.info(
            "Session manager initialized (max=%d, ttl=%ds)",
            max_sessions,
            session_ttl,
        )

    @property
    def active_count(self) -> int:
        """Return the number of active sessions."""
        return len(self._sessions)

    async def get_or_create(
        self,
        jwt_token: str,
        username: str,
        refresh_token: Optional[str] = None,
    ) -> CyberArkMCPServer:
        """Get an existing session or create a new one.

        Args:
            jwt_token: Raw JWT access token string.
            username: Username associated with the token.
            refresh_token: Optional OAuth refresh token.

        Returns:
            CyberArkMCPServer instance for this user's session.
        """
        session_key = hashlib.sha256(jwt_token.encode()).hexdigest()

        # Check for existing valid session
        if session_key in self._sessions:
            session = self._sessions[session_key]
            if not self._is_expired(session):
                logger.debug("Returning cached session for user: %s", username)
                return session["server"]
            else:
                # Expired — remove and recreate
                logger.info("Session expired for user: %s, recreating", username)
                self._evict(session_key)

        # Enforce max_sessions by evicting oldest
        while len(self._sessions) >= self._max_sessions:
            self._evict_oldest()

        # Create new session
        server = CyberArkMCPServer.from_token(
            jwt_token=jwt_token,
            username=username,
            refresh_token=refresh_token,
        )

        self._sessions[session_key] = {
            "server": server,
            "username": username,
            "created_at": time.time(),
        }

        logger.info(
            "Created new session for user: %s (active: %d/%d)",
            username,
            len(self._sessions),
            self._max_sessions,
        )

        return server

    def cleanup_expired(self) -> int:
        """Remove all expired sessions.

        Returns:
            Number of sessions removed.
        """
        expired_keys = [
            key
            for key, session in self._sessions.items()
            if self._is_expired(session)
        ]

        for key in expired_keys:
            self._evict(key)

        if expired_keys:
            logger.info(
                "Cleaned up %d expired sessions (active: %d)",
                len(expired_keys),
                len(self._sessions),
            )

        return len(expired_keys)

    async def shutdown(self) -> None:
        """Gracefully shut down all sessions."""
        logger.info("Shutting down %d sessions...", len(self._sessions))

        for key, session in list(self._sessions.items()):
            server = session["server"]
            if hasattr(server, "_executor"):
                server._executor.shutdown(wait=False)

        self._sessions.clear()
        logger.info("All sessions shut down")

    def _is_expired(self, session: Dict[str, Any]) -> bool:
        """Check if a session has exceeded its TTL."""
        return (time.time() - session["created_at"]) > self._session_ttl

    def _evict(self, session_key: str) -> None:
        """Remove a session by key, shutting down its executor."""
        session = self._sessions.pop(session_key, None)
        if session:
            server = session["server"]
            if hasattr(server, "_executor"):
                server._executor.shutdown(wait=False)
            logger.debug(
                "Evicted session for user: %s", session.get("username", "unknown")
            )

    def _evict_oldest(self) -> None:
        """Evict the session with the oldest created_at timestamp."""
        if not self._sessions:
            return

        oldest_key = min(
            self._sessions,
            key=lambda k: self._sessions[k]["created_at"],
        )
        logger.info(
            "Evicting oldest session: user=%s",
            self._sessions[oldest_key].get("username", "unknown"),
        )
        self._evict(oldest_key)
