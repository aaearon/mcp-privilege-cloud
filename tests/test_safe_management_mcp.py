#!/usr/bin/env python3
"""
Test Safe Management MCP Tools Integration

Tests the MCP tool wrappers for safe management functionality,
ensuring proper parameter passing and error handling.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cyberark_mcp.mcp_server import list_safes as mcp_list_safes
from cyberark_mcp.mcp_server import get_safe_details as mcp_get_safe_details


class TestSafeManagementMCP:
    """Test safe management MCP tool integration"""

    @pytest.mark.asyncio
    async def test_mcp_list_safes_basic(self):
        """Test MCP list_safes tool with basic usage"""
        mock_safes = [
            {"safeName": "HRSafe", "description": "HR Safe"},
            {"safeName": "ITSafe", "description": "IT Safe"}
        ]
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.list_safes.return_value = mock_safes
            mock_from_env.return_value = mock_server
            
            result = await mcp_list_safes()
            
            mock_server.list_safes.assert_called_once_with(
                search=None,
                offset=None,
                limit=None,
                sort=None,
                include_accounts=None,
                extended_details=None
            )
            assert result == mock_safes

    @pytest.mark.asyncio
    async def test_mcp_list_safes_with_parameters(self):
        """Test MCP list_safes tool with all parameters"""
        mock_safes = [{"safeName": "HRSafe"}]
        
        params = {
            "search": "HR",
            "offset": 10,
            "limit": 5,
            "sort": "safeName desc",
            "include_accounts": True,
            "extended_details": False
        }
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.list_safes.return_value = mock_safes
            mock_from_env.return_value = mock_server
            
            result = await mcp_list_safes(**params)
            
            mock_server.list_safes.assert_called_once_with(**params)
            assert result == mock_safes

    @pytest.mark.asyncio
    async def test_mcp_list_safes_error_handling(self):
        """Test MCP list_safes tool error handling"""
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.list_safes.side_effect = Exception("API Error")
            mock_from_env.return_value = mock_server
            
            with pytest.raises(Exception, match="API Error"):
                await mcp_list_safes()

    @pytest.mark.asyncio
    async def test_mcp_get_safe_details_basic(self):
        """Test MCP get_safe_details tool with basic usage"""
        safe_name = "HRSafe"
        mock_safe = {
            "safeName": safe_name,
            "description": "HR Safe",
            "accounts": []
        }
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.get_safe_details.return_value = mock_safe
            mock_from_env.return_value = mock_server
            
            result = await mcp_get_safe_details(safe_name)
            
            mock_server.get_safe_details.assert_called_once_with(
                safe_name,
                include_accounts=None,
                use_cache=None
            )
            assert result == mock_safe

    @pytest.mark.asyncio
    async def test_mcp_get_safe_details_with_parameters(self):
        """Test MCP get_safe_details tool with parameters"""
        safe_name = "HRSafe"
        mock_safe = {
            "safeName": safe_name,
            "accounts": [{"id": "123", "name": "hr-admin"}]
        }
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.get_safe_details.return_value = mock_safe
            mock_from_env.return_value = mock_server
            
            result = await mcp_get_safe_details(
                safe_name,
                include_accounts=True,
                use_cache=False
            )
            
            mock_server.get_safe_details.assert_called_once_with(
                safe_name,
                include_accounts=True,
                use_cache=False
            )
            assert result == mock_safe

    @pytest.mark.asyncio
    async def test_mcp_get_safe_details_error_handling(self):
        """Test MCP get_safe_details tool error handling"""
        safe_name = "NonExistentSafe"
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.get_safe_details.side_effect = Exception("Safe not found")
            mock_from_env.return_value = mock_server
            
            with pytest.raises(Exception, match="Safe not found"):
                await mcp_get_safe_details(safe_name)

    @pytest.mark.asyncio
    async def test_mcp_list_safes_pagination_scenario(self):
        """Test MCP list_safes with pagination parameters"""
        # Simulate a paginated request
        mock_safes = [{"safeName": f"Safe{i}"} for i in range(10)]
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.list_safes.return_value = mock_safes
            mock_from_env.return_value = mock_server
            
            result = await mcp_list_safes(
                offset=20,
                limit=10,
                sort="safeName asc"
            )
            
            mock_server.list_safes.assert_called_once_with(
                search=None,
                offset=20,
                limit=10,
                sort="safeName asc",
                include_accounts=None,
                extended_details=None
            )
            assert len(result) == 10

    @pytest.mark.asyncio
    async def test_mcp_get_safe_details_with_special_characters(self):
        """Test MCP get_safe_details with safe names containing special characters"""
        safe_name = "My Safe With Spaces & Special Characters"
        mock_safe = {"safeName": safe_name}
        
        with patch('cyberark_mcp.mcp_server.CyberArkMCPServer.from_environment') as mock_from_env:
            mock_server = AsyncMock()
            mock_server.get_safe_details.return_value = mock_safe
            mock_from_env.return_value = mock_server
            
            result = await mcp_get_safe_details(safe_name)
            
            # Verify the safe name is passed through correctly
            mock_server.get_safe_details.assert_called_once_with(
                safe_name,
                include_accounts=None,
                use_cache=None
            )
            assert result == mock_safe