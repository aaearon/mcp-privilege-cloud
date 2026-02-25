"""Tests for UserSessionManager.

Tests per-user session lifecycle management including creation, retrieval,
TTL expiry, max_sessions limits, and cleanup.
"""

import asyncio
import base64
import hashlib
import json
import time

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_jwt(claims: dict, header: dict | None = None) -> str:
    """Create a minimal JWT string (unsigned) for testing."""
    if header is None:
        header = {"alg": "RS256", "typ": "JWT", "kid": "test-key-id"}
    h = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    s = base64.urlsafe_b64encode(b"fakesig").rstrip(b"=").decode()
    return f"{h}.{p}.{s}"


def _default_claims(username: str = "testuser@abc1234.cyberark.cloud", **overrides) -> dict:
    """Return default valid JWT claims with optional overrides."""
    claims = {
        "sub": f"{username}.12345",
        "iss": "https://abc1234.id.cyberark.cloud/",
        "aud": "test-app-id",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "unique_name": username,
        "subdomain": "abc1234",
        "platform_domain": "cyberark.cloud",
    }
    claims.update(overrides)
    return claims


class TestUserSessionManagerInit:
    """Test UserSessionManager initialization."""

    def test_default_config(self):
        """Manager should initialize with sensible defaults."""
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager()

        assert manager._max_sessions == 100
        assert manager._session_ttl == 3600

    def test_custom_config(self):
        """Manager should accept custom max_sessions and session_ttl."""
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager(max_sessions=50, session_ttl=1800)

        assert manager._max_sessions == 50
        assert manager._session_ttl == 1800

    def test_sessions_dict_initially_empty(self):
        """Sessions cache should start empty."""
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager()

        assert len(manager._sessions) == 0


class TestUserSessionManagerGetOrCreate:
    """Test session creation and retrieval."""

    @pytest.mark.asyncio
    async def test_creates_new_session(self):
        """get_or_create should create a new session for a new token."""
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager()
        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        with patch(
            "mcp_privilege_cloud.session_manager.CyberArkMCPServer.from_token"
        ) as mock_from_token:
            mock_server = MagicMock()
            mock_from_token.return_value = mock_server

            server = await manager.get_or_create(
                jwt_token=jwt_token,
                username=claims["unique_name"],
            )

        assert server is mock_server
        assert len(manager._sessions) == 1

    @pytest.mark.asyncio
    async def test_returns_cached_session(self):
        """get_or_create should return cached session for same token."""
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager()
        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        with patch(
            "mcp_privilege_cloud.session_manager.CyberArkMCPServer.from_token"
        ) as mock_from_token:
            mock_server = MagicMock()
            mock_from_token.return_value = mock_server

            server1 = await manager.get_or_create(
                jwt_token=jwt_token,
                username=claims["unique_name"],
            )
            server2 = await manager.get_or_create(
                jwt_token=jwt_token,
                username=claims["unique_name"],
            )

        assert server1 is server2
        # from_token should only be called once
        mock_from_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_different_tokens_different_sessions(self):
        """Different tokens should create different sessions."""
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager()

        claims1 = _default_claims(username="user1@cyberark.cloud")
        jwt1 = _make_jwt(claims1)

        claims2 = _default_claims(username="user2@cyberark.cloud")
        jwt2 = _make_jwt(claims2)

        with patch(
            "mcp_privilege_cloud.session_manager.CyberArkMCPServer.from_token"
        ) as mock_from_token:
            mock_server1 = MagicMock()
            mock_server2 = MagicMock()
            mock_from_token.side_effect = [mock_server1, mock_server2]

            server1 = await manager.get_or_create(
                jwt_token=jwt1,
                username=claims1["unique_name"],
            )
            server2 = await manager.get_or_create(
                jwt_token=jwt2,
                username=claims2["unique_name"],
            )

        assert server1 is not server2
        assert len(manager._sessions) == 2

    @pytest.mark.asyncio
    async def test_session_key_is_sha256_of_token(self):
        """Session key should be SHA-256 hash of the JWT token."""
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager()
        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        expected_key = hashlib.sha256(jwt_token.encode()).hexdigest()

        with patch(
            "mcp_privilege_cloud.session_manager.CyberArkMCPServer.from_token"
        ) as mock_from_token:
            mock_from_token.return_value = MagicMock()
            await manager.get_or_create(
                jwt_token=jwt_token,
                username=claims["unique_name"],
            )

        assert expected_key in manager._sessions


class TestUserSessionManagerTTL:
    """Test session TTL expiry."""

    @pytest.mark.asyncio
    async def test_expired_session_recreated(self):
        """An expired session should be evicted and recreated."""
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager(session_ttl=1)
        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        with patch(
            "mcp_privilege_cloud.session_manager.CyberArkMCPServer.from_token"
        ) as mock_from_token:
            mock_server1 = MagicMock()
            mock_server2 = MagicMock()
            mock_from_token.side_effect = [mock_server1, mock_server2]

            server1 = await manager.get_or_create(
                jwt_token=jwt_token,
                username=claims["unique_name"],
            )

            # Manually expire the session by backdating created_at
            session_key = hashlib.sha256(jwt_token.encode()).hexdigest()
            manager._sessions[session_key]["created_at"] = time.time() - 10

            server2 = await manager.get_or_create(
                jwt_token=jwt_token,
                username=claims["unique_name"],
            )

        assert server1 is not server2
        assert mock_from_token.call_count == 2


class TestUserSessionManagerMaxSessions:
    """Test max_sessions limit enforcement."""

    @pytest.mark.asyncio
    async def test_max_sessions_evicts_oldest(self):
        """When max_sessions is reached, the oldest session should be evicted."""
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager(max_sessions=2)

        with patch(
            "mcp_privilege_cloud.session_manager.CyberArkMCPServer.from_token"
        ) as mock_from_token:
            mock_from_token.return_value = MagicMock()

            # Create 3 sessions (exceeds max of 2)
            for i in range(3):
                claims = _default_claims(username=f"user{i}@cyberark.cloud")
                jwt = _make_jwt(claims)
                await manager.get_or_create(
                    jwt_token=jwt,
                    username=claims["unique_name"],
                )

        # Should have evicted the oldest, leaving 2
        assert len(manager._sessions) == 2

    @pytest.mark.asyncio
    async def test_max_sessions_evicts_correct_session(self):
        """Eviction should remove the session with the oldest created_at."""
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager(max_sessions=2)

        with patch(
            "mcp_privilege_cloud.session_manager.CyberArkMCPServer.from_token"
        ) as mock_from_token:
            mock_from_token.return_value = MagicMock()

            # Create session 0
            claims0 = _default_claims(username="user0@cyberark.cloud")
            jwt0 = _make_jwt(claims0)
            await manager.get_or_create(jwt_token=jwt0, username=claims0["unique_name"])
            key0 = hashlib.sha256(jwt0.encode()).hexdigest()

            # Create session 1
            claims1 = _default_claims(username="user1@cyberark.cloud")
            jwt1 = _make_jwt(claims1)
            await manager.get_or_create(jwt_token=jwt1, username=claims1["unique_name"])

            # Create session 2 — should evict session 0
            claims2 = _default_claims(username="user2@cyberark.cloud")
            jwt2 = _make_jwt(claims2)
            await manager.get_or_create(jwt_token=jwt2, username=claims2["unique_name"])

        assert key0 not in manager._sessions


class TestUserSessionManagerCleanup:
    """Test expired session cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_removes_expired(self):
        """cleanup_expired should remove sessions past their TTL."""
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager(session_ttl=1)
        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        with patch(
            "mcp_privilege_cloud.session_manager.CyberArkMCPServer.from_token"
        ) as mock_from_token:
            mock_from_token.return_value = MagicMock()

            await manager.get_or_create(
                jwt_token=jwt_token,
                username=claims["unique_name"],
            )

        # Backdate the session
        session_key = hashlib.sha256(jwt_token.encode()).hexdigest()
        manager._sessions[session_key]["created_at"] = time.time() - 10

        removed = manager.cleanup_expired()

        assert removed == 1
        assert len(manager._sessions) == 0

    @pytest.mark.asyncio
    async def test_cleanup_keeps_valid(self):
        """cleanup_expired should keep sessions within their TTL."""
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager(session_ttl=3600)
        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        with patch(
            "mcp_privilege_cloud.session_manager.CyberArkMCPServer.from_token"
        ) as mock_from_token:
            mock_from_token.return_value = MagicMock()

            await manager.get_or_create(
                jwt_token=jwt_token,
                username=claims["unique_name"],
            )

        removed = manager.cleanup_expired()

        assert removed == 0
        assert len(manager._sessions) == 1


class TestUserSessionManagerShutdown:
    """Test graceful shutdown."""

    @pytest.mark.asyncio
    async def test_shutdown_clears_sessions(self):
        """shutdown should clear all sessions."""
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager()
        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        with patch(
            "mcp_privilege_cloud.session_manager.CyberArkMCPServer.from_token"
        ) as mock_from_token:
            mock_server = MagicMock()
            mock_from_token.return_value = mock_server

            await manager.get_or_create(
                jwt_token=jwt_token,
                username=claims["unique_name"],
            )

        await manager.shutdown()

        assert len(manager._sessions) == 0

    @pytest.mark.asyncio
    async def test_shutdown_calls_executor_shutdown(self):
        """shutdown should shut down executors on cached servers."""
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager()
        claims = _default_claims()
        jwt_token = _make_jwt(claims)

        with patch(
            "mcp_privilege_cloud.session_manager.CyberArkMCPServer.from_token"
        ) as mock_from_token:
            mock_server = MagicMock()
            mock_server._executor = MagicMock()
            mock_from_token.return_value = mock_server

            await manager.get_or_create(
                jwt_token=jwt_token,
                username=claims["unique_name"],
            )

        await manager.shutdown()

        mock_server._executor.shutdown.assert_called_once_with(wait=False)


class TestUserSessionManagerActiveCount:
    """Test active session counting."""

    @pytest.mark.asyncio
    async def test_active_count(self):
        """active_count should return the number of active sessions."""
        from mcp_privilege_cloud.session_manager import UserSessionManager

        manager = UserSessionManager()

        assert manager.active_count == 0

        with patch(
            "mcp_privilege_cloud.session_manager.CyberArkMCPServer.from_token"
        ) as mock_from_token:
            mock_from_token.return_value = MagicMock()

            for i in range(3):
                claims = _default_claims(username=f"user{i}@cyberark.cloud")
                jwt = _make_jwt(claims)
                await manager.get_or_create(
                    jwt_token=jwt,
                    username=claims["unique_name"],
                )

        assert manager.active_count == 3
