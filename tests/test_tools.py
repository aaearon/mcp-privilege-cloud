"""
Tests for CyberArk MCP tools.

This module provides comprehensive tests for all tool functions including
parameter validation, error handling, and integration with the MCP server.
"""

import pytest
from unittest.mock import AsyncMock, patch

# Import the new tool functions
from mcp_privilege_cloud.mcp_server import (
    list_accounts, search_accounts, list_safes, list_platforms
)


class TestAccountTools:
    """Test account-related tool functions."""
    
    @pytest.mark.asyncio
    async def test_list_accounts_success(self):
        """Test successful account listing."""
        mock_accounts = [
            {
                "id": "123_456",
                "name": "admin@server01",
                "address": "server01.corp.com",
                "userName": "admin",
                "platformId": "WinServerLocal",
                "safeName": "IT-Infrastructure",
                "secretType": "password",
                "createdTime": "2025-06-09T10:30:00Z"
            }
        ]
        
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            mock_server = AsyncMock()
            mock_server.list_accounts.return_value = mock_accounts
            mock_server_factory.return_value = mock_server
            
            result = await list_accounts()
            
            assert result == mock_accounts
            mock_server.list_accounts.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_accounts_with_query(self):
        """Test account search with query parameters."""
        mock_accounts = [
            {
                "id": "123_456",
                "name": "admin@server01",
                "address": "server01.corp.com",
                "userName": "admin",
                "platformId": "WinServerLocal",
                "safeName": "IT-Infrastructure",
                "_score": 0.85
            }
        ]
        
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            mock_server = AsyncMock()
            mock_server.search_accounts.return_value = mock_accounts
            mock_server_factory.return_value = mock_server
            
            result = await search_accounts(
                query="admin",
                safe_name="IT-Infrastructure",
                platform_id="WinServerLocal"
            )
            
            assert result == mock_accounts
            mock_server.search_accounts.assert_called_once_with(
                keywords="admin",
                safe_name="IT-Infrastructure",
                username=None,
                address=None,
                platform_id="WinServerLocal"
            )

    @pytest.mark.asyncio
    async def test_search_accounts_no_params(self):
        """Test account search with no parameters."""
        mock_accounts = []
        
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            mock_server = AsyncMock()
            mock_server.search_accounts.return_value = mock_accounts
            mock_server_factory.return_value = mock_server
            
            result = await search_accounts()
            
            assert result == mock_accounts
            mock_server.search_accounts.assert_called_once_with(
                keywords=None,
                safe_name=None,
                username=None,
                address=None,
                platform_id=None
            )


class TestSafeTools:
    """Test safe-related tool functions."""
    
    @pytest.mark.asyncio
    async def test_list_safes_success(self):
        """Test successful safe listing."""
        mock_safes = [
            {
                "safeName": "IT-Infrastructure",
                "safeNumber": 123,
                "description": "IT Infrastructure accounts",
                "location": "\\Root",
                "createdBy": "Administrator",
                "creationTime": "2025-01-01T00:00:00Z",
                "managingCPM": "PasswordManager",
                "numberOfVersionsRetention": 7,
                "numberOfDaysRetention": 365,
                "autoPurgeEnabled": False
            }
        ]
        
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            mock_server = AsyncMock()
            mock_server.list_safes.return_value = mock_safes
            mock_server_factory.return_value = mock_server
            
            result = await list_safes()
            
            assert result == mock_safes
            mock_server.list_safes.assert_called_once()


class TestPlatformTools:
    """Test platform-related tool functions."""
    
    @pytest.mark.asyncio
    async def test_list_platforms_success(self):
        """Test successful platform listing."""
        mock_platforms = [
            {
                "id": "WinServerLocal",
                "name": "Windows Server Local",
                "systemType": "Windows",
                "active": True,
                "platformType": "Regular",
                "description": "Windows Server Local Accounts",
                "platformBaseID": "WinDomain",
                "duplicatesAllowed": True,
                "independentPasswordPolicy": True,
                "createdBy": "Administrator",
                "creationDate": "2025-01-01T00:00:00Z"
            }
        ]
        
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            mock_server = AsyncMock()
            mock_server.list_platforms.return_value = mock_platforms
            mock_server_factory.return_value = mock_server
            
            result = await list_platforms()
            
            assert result == mock_platforms
            mock_server.list_platforms.assert_called_once()


class TestToolErrorHandling:
    """Test error handling for all tool functions."""
    
    @pytest.mark.asyncio
    async def test_list_accounts_error(self):
        """Test error handling in list_accounts."""
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            mock_server = AsyncMock()
            mock_server.list_accounts.side_effect = Exception("API Error")
            mock_server_factory.return_value = mock_server
            
            with pytest.raises(Exception, match="API Error"):
                await list_accounts()

    @pytest.mark.asyncio
    async def test_search_accounts_error(self):
        """Test error handling in search_accounts."""
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            mock_server = AsyncMock()
            mock_server.search_accounts.side_effect = Exception("API Error")
            mock_server_factory.return_value = mock_server
            
            with pytest.raises(Exception, match="API Error"):
                await search_accounts(query="test")

    @pytest.mark.asyncio
    async def test_list_safes_error(self):
        """Test error handling in list_safes."""
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            mock_server = AsyncMock()
            mock_server.list_safes.side_effect = Exception("API Error")
            mock_server_factory.return_value = mock_server
            
            with pytest.raises(Exception, match="API Error"):
                await list_safes()

    @pytest.mark.asyncio
    async def test_list_platforms_error(self):
        """Test error handling in list_platforms."""
        with patch('mcp_privilege_cloud.mcp_server.CyberArkMCPServer.from_environment') as mock_server_factory:
            mock_server = AsyncMock()
            mock_server.list_platforms.side_effect = Exception("API Error")
            mock_server_factory.return_value = mock_server
            
            with pytest.raises(Exception, match="API Error"):
                await list_platforms()