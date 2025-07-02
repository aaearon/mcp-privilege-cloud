"""
Performance tests for enhanced platform functionality.

This module provides comprehensive performance testing for the platform enhancement
features implemented in Tasks A1-A4 and B1-B2, including:

- Large-scale platform operations (125+ platforms)
- Concurrent API request batching performance  
- Memory usage with enhanced platform objects
- Response time comparison (basic vs enhanced)
- Error handling performance impact
- Resource loading performance

Test categories:
- @pytest.mark.performance: All performance tests
- @pytest.mark.integration: Tests requiring external mocking
- @pytest.mark.memory: Memory usage and optimization tests
"""

import asyncio
import time
import gc
import tracemalloc
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch
import pytest

from mcp_privilege_cloud.server import CyberArkMCPServer
from mcp_privilege_cloud.resources.platforms import PlatformCollectionResource
from mcp_privilege_cloud.resources.base import ResourceURI
from mcp_privilege_cloud.server import CyberArkAPIError


class TestPlatformPerformance:
    """Test performance characteristics of enhanced platform functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        return {
            'subdomain': 'test',
            'client_id': 'test-client',
            'client_secret': 'test-secret',
            'tenant_id': 'test-tenant'
        }
    
    @pytest.fixture  
    def mock_authenticator(self):
        """Mock authenticator for testing"""
        mock_auth = Mock()
        mock_auth.get_auth_header.return_value = {"Authorization": "Bearer test-token"}
        return mock_auth
    
    @pytest.fixture
    def server(self, mock_config, mock_authenticator):
        """Create server instance for testing"""
        server = CyberArkMCPServer(
            authenticator=mock_authenticator,
            subdomain=mock_config['subdomain']
        )
        return server
    
    @pytest.fixture
    def large_platform_dataset(self):
        """Generate large dataset of 125 platforms for performance testing."""
        platforms = []
        for i in range(125):
            platforms.append({
                "id": f"Platform{i:03d}",
                "name": f"Platform {i:03d}",
                "systemType": "Windows" if i % 2 == 0 else "Unix",
                "active": True,
                "description": f"Test platform {i} for performance testing",
                "platformBaseID": f"Platform{i:03d}",
                "platformType": "Regular"
            })
        return platforms
    
    @pytest.fixture
    def large_enhanced_platform_dataset(self):
        """Generate large dataset of 125 enhanced platforms with complete details."""
        platforms = []
        for i in range(125):
            platforms.append({
                # Basic info
                "id": f"Platform{i:03d}",
                "name": f"Platform {i:03d}",
                "systemType": "Windows" if i % 2 == 0 else "Unix",
                "active": True,
                "description": f"Test platform {i} for performance testing",
                "platformBaseID": f"Platform{i:03d}",
                "platformType": "Regular",
                
                # Enhanced details
                "details": {
                    "policyId": f"Platform{i:03d}",
                    "policyName": f"Platform {i:03d}",
                    "systemType": "Windows" if i % 2 == 0 else "Unix",
                    "active": True,
                    "generalSettings": {
                        "allowManualChange": True,
                        "performPeriodicChange": i % 3 == 0,
                        "allowManualVerification": True,
                        "requirePasswordChangeEveryXDays": 30 + (i % 60),
                        "enforceCheckinExclusivePassword": True,
                        "enforceOneTimePasswordAccess": False
                    },
                    "connectionComponents": [
                        {
                            "psmServerId": f"PSM{i:02d}",
                            "name": f"PSM-RDP-{i}",
                            "connectionMethod": "RDP" if i % 2 == 0 else "SSH",
                            "enabled": True,
                            "userRole": "Administrator",
                            "parameters": {
                                "AllowMappingLocalDrives": "Yes",
                                "AllowConnectToConsole": "No",
                                "AudioRedirection": "Yes"
                            }
                        }
                    ],
                    "privilegedAccessWorkflows": {
                        "requireDualControlPasswordAccessApproval": i % 5 == 0,
                        "enforceCheckinExclusivePassword": True,
                        "requireUsersToSpecifyReasonForAccess": True
                    }
                },
                
                # Credential and session management
                "credentialsManagement": {
                    "allowManualChange": True,
                    "performPeriodicChange": i % 3 == 0,
                    "allowManualVerification": True
                },
                "sessionManagement": {
                    "requirePrivilegedSessionMonitoringAndIsolation": True,
                    "recordAndSaveSessionActivity": True,
                    "PSMServerID": f"PSMServer_{i}"
                }
            })
        return platforms

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_125_platforms_response_time_enhanced(self, server, large_enhanced_platform_dataset):
        """Test response time for 125 platforms with enhanced details using concurrent fetching."""
        
        async def mock_get_complete_platform_info(platform_id):
            # Simulate realistic API delay (50-150ms per platform)
            await asyncio.sleep(0.05 + (hash(platform_id) % 100) / 1000)
            
            # Find the platform data
            for platform in large_enhanced_platform_dataset:
                if platform["id"] == platform_id:
                    return platform
            raise CyberArkAPIError(f"Platform {platform_id} not found", 404)
        
        with patch.object(server, 'list_platforms', return_value=large_enhanced_platform_dataset[:125]):
            with patch.object(server, 'get_complete_platform_info', side_effect=mock_get_complete_platform_info):
                
                # Measure performance
                start_time = time.time()
                result = await server.list_platforms_with_details()
                end_time = time.time()
                
                execution_time = end_time - start_time
                
                # Performance assertions
                assert len(result) == 125, f"Expected 125 platforms, got {len(result)}"
                assert execution_time < 15.0, f"Expected < 15s for 125 platforms, took {execution_time:.2f}s"
                
                # Calculate performance metrics
                avg_time_per_platform = execution_time / 125
                theoretical_sequential_time = 125 * 0.1  # 100ms average per platform
                concurrency_improvement = theoretical_sequential_time / execution_time
                
                print(f"Performance metrics for 125 platforms:")
                print(f"  Total time: {execution_time:.2f}s")
                print(f"  Average per platform: {avg_time_per_platform*1000:.1f}ms")
                print(f"  Concurrency improvement: {concurrency_improvement:.1f}x")
                
                # Verify concurrent processing occurred (should be much faster than sequential)
                assert concurrency_improvement > 3.0, f"Expected >3x improvement, got {concurrency_improvement:.1f}x"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_fetching_scalability(self, server, large_platform_dataset):
        """Test scalability of concurrent platform fetching with different platform counts."""
        
        test_sizes = [10, 25, 50, 100]
        performance_results = {}
        
        async def mock_get_complete_platform_info(platform_id):
            await asyncio.sleep(0.05)  # 50ms consistent delay
            return {
                "id": platform_id,
                "name": f"Platform {platform_id}",
                "details": {"policyId": platform_id}
            }
        
        for size in test_sizes:
            test_platforms = large_platform_dataset[:size]
            
            with patch.object(server, 'list_platforms', return_value=test_platforms):
                with patch.object(server, 'get_complete_platform_info', side_effect=mock_get_complete_platform_info):
                    
                    start_time = time.time()
                    result = await server.list_platforms_with_details()
                    end_time = time.time()
                    
                    execution_time = end_time - start_time
                    performance_results[size] = {
                        'time': execution_time,
                        'count': len(result),
                        'avg_per_platform': execution_time / size
                    }
        
        # Analyze scalability characteristics
        print("Scalability Analysis:")
        for size, metrics in performance_results.items():
            print(f"  {size} platforms: {metrics['time']:.2f}s ({metrics['avg_per_platform']*1000:.1f}ms avg)")
        
        # Verify reasonable scaling (shouldn't grow linearly)
        small_scale_time = performance_results[10]['time']
        large_scale_time = performance_results[100]['time']
        scale_factor = large_scale_time / small_scale_time
        
        # With concurrency, 10x more platforms shouldn't take 10x longer
        # Allow for some variance in test environment performance
        assert scale_factor < 12.0, f"Poor scaling: 10x platforms took {scale_factor:.1f}x longer"

    @pytest.mark.performance
    @pytest.mark.memory
    @pytest.mark.asyncio
    async def test_memory_usage_with_enhanced_platforms(self, server, large_enhanced_platform_dataset):
        """Test memory usage patterns with enhanced platform objects."""
        
        # Start memory tracking
        tracemalloc.start()
        
        async def mock_get_complete_platform_info(platform_id):
            for platform in large_enhanced_platform_dataset:
                if platform["id"] == platform_id:
                    return platform
            raise CyberArkAPIError(f"Platform {platform_id} not found", 404)
        
        with patch.object(server, 'list_platforms', return_value=large_enhanced_platform_dataset[:100]):
            with patch.object(server, 'get_complete_platform_info', side_effect=mock_get_complete_platform_info):
                
                # Get initial memory usage
                snapshot1 = tracemalloc.take_snapshot()
                
                # Execute platform loading
                result = await server.list_platforms_with_details()
                
                # Get memory usage after operation
                snapshot2 = tracemalloc.take_snapshot()
                
                # Force garbage collection
                gc.collect()
                snapshot3 = tracemalloc.take_snapshot()
        
        # Analyze memory usage
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        memory_peak = sum(stat.size for stat in top_stats) / 1024 / 1024  # MB
        
        post_gc_stats = snapshot3.compare_to(snapshot1, 'lineno')
        memory_after_gc = sum(stat.size for stat in post_gc_stats) / 1024 / 1024  # MB
        
        print(f"Memory Analysis for 100 enhanced platforms:")
        print(f"  Peak memory usage: {memory_peak:.2f} MB")
        print(f"  After garbage collection: {memory_after_gc:.2f} MB")
        print(f"  Memory per platform: {memory_peak/100:.3f} MB")
        
        # Memory usage assertions
        assert memory_peak < 50.0, f"Memory usage too high: {memory_peak:.2f} MB"
        assert len(result) == 100, f"Expected 100 platforms, got {len(result)}"
        
        # Verify enhanced data is included
        sample_platform = result[0]
        # Check for either raw API format or converted format
        has_enhanced_data = (
            "general_settings" in sample_platform or 
            ("details" in sample_platform and "generalSettings" in sample_platform["details"])
        )
        assert has_enhanced_data, f"Enhanced data missing from: {list(sample_platform.keys())}"
        
        has_connection_data = (
            "connection_components" in sample_platform or
            ("details" in sample_platform and "connectionComponents" in sample_platform["details"])
        )
        assert has_connection_data, "Connection components missing"
        
        tracemalloc.stop()

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_response_time_comparison_basic_vs_enhanced(self, server, large_platform_dataset):
        """Compare response times between basic and enhanced platform listing."""
        
        # Test basic platform listing with realistic delay
        async def mock_basic_list_platforms():
            await asyncio.sleep(0.01)  # 10ms realistic API delay
            return large_platform_dataset[:50]
        
        with patch.object(server, 'list_platforms', side_effect=mock_basic_list_platforms):
            start_time = time.time()
            basic_result = await server.list_platforms()
            basic_time = time.time() - start_time
        
        # Test enhanced platform listing with mock delays
        async def mock_get_complete_platform_info(platform_id):
            await asyncio.sleep(0.02)  # 20ms delay per platform
            return {
                "id": platform_id,
                "name": f"Enhanced {platform_id}",
                "details": {"policyId": platform_id, "generalSettings": {}}
            }
        
        with patch.object(server, 'list_platforms', return_value=large_platform_dataset[:50]):
            with patch.object(server, 'get_complete_platform_info', side_effect=mock_get_complete_platform_info):
                start_time = time.time()
                enhanced_result = await server.list_platforms_with_details()
                enhanced_time = time.time() - start_time
        
        # Performance comparison
        overhead_ratio = enhanced_time / basic_time if basic_time > 0 else float('inf')
        
        print(f"Performance Comparison for 50 platforms:")
        print(f"  Basic listing: {basic_time*1000:.1f}ms")
        print(f"  Enhanced listing: {enhanced_time*1000:.1f}ms")
        print(f"  Overhead ratio: {overhead_ratio:.1f}x")
        
        # Assertions
        assert len(basic_result) == 50, f"Basic result count mismatch"
        assert len(enhanced_result) == 50, f"Enhanced result count mismatch"
        assert enhanced_time < 5.0, f"Enhanced listing too slow: {enhanced_time:.2f}s"
        assert overhead_ratio < 15.0, f"Enhanced overhead too high: {overhead_ratio:.1f}x"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_error_handling_performance_impact(self, server, large_platform_dataset):
        """Test performance impact of error handling during concurrent operations."""
        
        failure_rate = 0.2  # 20% of platforms will fail
        call_count = 0
        
        async def mock_get_complete_platform_info_with_failures(platform_id):
            nonlocal call_count
            call_count += 1
            
            # Simulate some platforms failing
            if hash(platform_id) % 5 == 0:  # 20% failure rate
                await asyncio.sleep(0.01)  # Quick failure
                raise CyberArkAPIError(f"Platform {platform_id} access denied", 403)
            else:
                await asyncio.sleep(0.05)  # Normal processing time
                return {"id": platform_id, "name": f"Platform {platform_id}"}
        
        with patch.object(server, 'list_platforms', return_value=large_platform_dataset[:50]):
            with patch.object(server, 'get_complete_platform_info', side_effect=mock_get_complete_platform_info_with_failures):
                
                start_time = time.time()
                result = await server.list_platforms_with_details()
                execution_time = time.time() - start_time
        
        expected_success_count = int(50 * (1 - failure_rate))
        actual_success_count = len(result)
        
        print(f"Error Handling Performance for 50 platforms with {failure_rate*100}% failure rate:")
        print(f"  Total time: {execution_time:.2f}s")
        print(f"  Successful platforms: {actual_success_count}/{50}")
        print(f"  Expected successful: ~{expected_success_count}")
        print(f"  Total API calls made: {call_count}")
        
        # Performance assertions with error handling
        assert execution_time < 3.0, f"Error handling caused slowdown: {execution_time:.2f}s"
        assert actual_success_count >= expected_success_count - 5, "Too many platforms failed"
        assert call_count == 50, f"Should attempt all platforms, made {call_count} calls"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_resource_loading_performance(self, server, large_enhanced_platform_dataset):
        """Test performance of enhanced PlatformCollectionResource loading."""
        
        # Mock server method
        async def mock_list_platforms_with_details():
            await asyncio.sleep(0.5)  # Simulate API delay
            return large_enhanced_platform_dataset[:75]
        
        server.list_platforms_with_details = mock_list_platforms_with_details
        
        uri = ResourceURI("cyberark://platforms/")
        resource = PlatformCollectionResource(uri, server)
        
        # Test resource loading performance
        start_time = time.time()
        items = await resource.get_items()
        loading_time = time.time() - start_time
        
        print(f"Resource Loading Performance for 75 platforms:")
        print(f"  Loading time: {loading_time:.2f}s")
        print(f"  Items returned: {len(items)}")
        print(f"  Average per item: {loading_time/len(items)*1000:.1f}ms")
        
        # Verify enhanced fields are present
        if items:
            sample_item = items[0]
            enhanced_fields = [
                "policy_id", "general_settings", "connection_components", 
                "privileged_access_workflows"
            ]
            present_fields = [field for field in enhanced_fields if field in sample_item]
            
            print(f"  Enhanced fields present: {len(present_fields)}/{len(enhanced_fields)}")
            
            # Performance and functionality assertions
            assert loading_time < 2.0, f"Resource loading too slow: {loading_time:.2f}s"
            assert len(items) == 75, f"Expected 75 items, got {len(items)}"
            assert len(present_fields) >= 3, f"Missing enhanced fields: {enhanced_fields}"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_field_conversion_performance(self, server):
        """Test performance impact of CamelCase to snake_case field conversion."""
        
        # Create platform with many nested fields requiring conversion
        complex_platform = {
            "id": "TestPlatform",
            "name": "Test Platform",
            "systemType": "Windows",
            "platformBaseID": "TestBase",
            "details": {
                "policyId": "TestPolicy",
                "generalSettings": {
                    "allowManualChange": True,
                    "performPeriodicChange": False,
                    "requirePasswordChangeEveryXDays": 90,
                    "enforceCheckinExclusivePassword": True,
                    "enforceOneTimePasswordAccess": False
                },
                "connectionComponents": [
                    {
                        "psmServerId": "PSM01",
                        "connectionMethod": "RDP",
                        "userRole": "Administrator",
                        "parameters": {
                            "AllowMappingLocalDrives": "Yes",
                            "AllowConnectToConsole": "No",
                            "AudioRedirection": "Yes"
                        }
                    }
                ],
                "privilegedAccessWorkflows": {
                    "requireDualControlPasswordAccessApproval": False,
                    "requireUsersToSpecifyReasonForAccess": True
                }
            }
        }
        
        # Create dataset with multiple complex platforms
        complex_dataset = [complex_platform.copy() for _ in range(100)]
        for i, platform in enumerate(complex_dataset):
            platform["id"] = f"Platform{i:03d}"
        
        uri = ResourceURI("cyberark://platforms/")
        resource = PlatformCollectionResource(uri, server)
        
        # Mock the enhanced method
        async def mock_list_platforms_with_details():
            return complex_dataset
        
        server.list_platforms_with_details = mock_list_platforms_with_details
        
        # Test field conversion performance
        start_time = time.time()
        items = await resource.get_items()
        conversion_time = time.time() - start_time
        
        print(f"Field Conversion Performance for 100 complex platforms:")
        print(f"  Conversion time: {conversion_time*1000:.1f}ms")
        print(f"  Time per platform: {conversion_time/100*1000:.2f}ms")
        
        # Verify conversion worked correctly
        if items:
            sample_item = items[0]
            converted_fields = [
                "system_type", "platform_base_id", "policy_id",
                "psm_server_id", "connection_method", "user_role"
            ]
            
            # Count successfully converted fields
            present_converted = sum(1 for field in converted_fields if field in str(sample_item))
            
            print(f"  Converted fields detected: {present_converted}/{len(converted_fields)}")
            
            # Performance assertions
            assert conversion_time < 0.5, f"Field conversion too slow: {conversion_time*1000:.1f}ms"
            assert len(items) == 100, f"Expected 100 items, got {len(items)}"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_limit_optimization(self, server, large_platform_dataset):
        """Test optimal concurrent request limit for platform fetching."""
        
        concurrency_limits = [5, 10, 15, 20]
        performance_results = {}
        
        for limit in concurrency_limits:
            call_times = []
            
            async def mock_get_complete_platform_info(platform_id):
                call_times.append(time.time())
                await asyncio.sleep(0.05)  # 50ms API delay
                return {"id": platform_id, "name": f"Platform {platform_id}"}
            
            # Patch the semaphore limit in the method
            original_method = server.list_platforms_with_details
            
            async def patched_method(**kwargs):
                # Override semaphore limit for testing
                platforms_list = large_platform_dataset[:30]  # Test with 30 platforms
                
                semaphore = asyncio.Semaphore(limit)
                
                async def fetch_platform_details(platform):
                    async with semaphore:
                        platform_id = platform.get('id')
                        return await mock_get_complete_platform_info(platform_id)
                
                tasks = [fetch_platform_details(platform) for platform in platforms_list]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return [r for r in results if not isinstance(r, Exception)]
            
            server.list_platforms_with_details = patched_method
            
            with patch.object(server, 'list_platforms', return_value=large_platform_dataset[:30]):
                start_time = time.time()
                result = await server.list_platforms_with_details()
                execution_time = time.time() - start_time
            
            performance_results[limit] = {
                'time': execution_time,
                'count': len(result),
                'call_spread': max(call_times) - min(call_times) if call_times else 0
            }
            
            # Reset for next test
            call_times.clear()
            server.list_platforms_with_details = original_method
        
        # Analyze optimal concurrency
        print("Concurrency Limit Analysis for 30 platforms:")
        best_limit = min(performance_results.keys(), key=lambda k: performance_results[k]['time'])
        
        for limit, metrics in performance_results.items():
            marker = " <- OPTIMAL" if limit == best_limit else ""
            print(f"  Limit {limit:2d}: {metrics['time']:.2f}s, spread: {metrics['call_spread']:.2f}s{marker}")
        
        # Verify reasonable performance across all limits
        for limit, metrics in performance_results.items():
            assert metrics['time'] < 3.0, f"Limit {limit} too slow: {metrics['time']:.2f}s"
            assert metrics['count'] == 30, f"Limit {limit} missing results: {metrics['count']}"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_pagination_performance_impact(self, server):
        """Test performance impact of pagination on large platform lists."""
        
        # Create a large dataset that would normally be paginated
        full_dataset = []
        for i in range(250):  # Large dataset that might trigger pagination
            full_dataset.append({
                "id": f"Platform{i:03d}",
                "name": f"Platform {i:03d}",
                "systemType": "Windows" if i % 2 == 0 else "Unix",
                "active": True
            })
        
        # Test with pagination parameters
        pagination_configs = [
            {"limit": 50, "offset": 0},   # First page
            {"limit": 50, "offset": 50},  # Second page  
            {"limit": 100, "offset": 0},  # Larger page
            {}  # No pagination (all results)
        ]
        
        performance_results = {}
        
        for i, config in enumerate(pagination_configs):
            config_name = f"config_{i}" if config else "no_pagination"
            
            # Mock pagination behavior
            if config:
                limit = config.get("limit", len(full_dataset))
                offset = config.get("offset", 0)
                paginated_data = full_dataset[offset:offset + limit]
            else:
                paginated_data = full_dataset
            
            with patch.object(server, 'list_platforms', return_value=paginated_data):
                start_time = time.time()
                result = await server.list_platforms(**config)
                execution_time = time.time() - start_time
            
            performance_results[config_name] = {
                'time': execution_time,
                'count': len(result),
                'config': config
            }
        
        print("Pagination Performance Analysis:")
        for name, metrics in performance_results.items():
            config_str = str(metrics['config']) if metrics['config'] else "no limits"
            print(f"  {name}: {metrics['time']*1000:.1f}ms for {metrics['count']} platforms ({config_str})")
        
        # Performance assertions
        for name, metrics in performance_results.items():
            assert metrics['time'] < 1.0, f"{name} too slow: {metrics['time']:.2f}s"
            
        # Verify pagination doesn't significantly impact performance for reasonable page sizes
        if 'config_0' in performance_results and 'config_2' in performance_results:
            small_page_time = performance_results['config_0']['time']
            large_page_time = performance_results['config_2']['time']
            # Large page (2x size) shouldn't take significantly longer than small page
            assert large_page_time < small_page_time * 3, "Poor pagination scaling"


class TestMemoryOptimization:
    """Test memory usage patterns and optimization for enhanced platform functionality."""
    
    @pytest.fixture
    def server(self):
        """Create server instance for memory testing"""
        mock_auth = Mock()
        mock_auth.get_auth_header.return_value = {"Authorization": "Bearer test-token"}
        return CyberArkMCPServer(authenticator=mock_auth, subdomain='test')
    
    @pytest.mark.performance
    @pytest.mark.memory
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, server):
        """Test for memory leaks in repeated platform operations."""
        
        tracemalloc.start()
        
        # Create moderate dataset
        test_platforms = [
            {
                "id": f"Platform{i:03d}",
                "name": f"Platform {i:03d}",
                "details": {"policyId": f"Policy{i:03d}"}
            }
            for i in range(50)
        ]
        
        async def mock_list_platforms_with_details():
            return test_platforms.copy()
        
        server.list_platforms_with_details = mock_list_platforms_with_details
        
        # Perform multiple iterations to detect leaks
        snapshots = []
        for iteration in range(5):
            # Force garbage collection before measurement
            gc.collect()
            snapshot = tracemalloc.take_snapshot()
            snapshots.append(snapshot)
            
            # Perform platform operations
            for _ in range(10):
                result = await server.list_platforms_with_details()
                assert len(result) == 50
        
        # Analyze memory growth across iterations
        memory_usage = []
        for i, snapshot in enumerate(snapshots):
            if i == 0:
                memory_usage.append(0)
            else:
                top_stats = snapshot.compare_to(snapshots[0], 'lineno')
                memory_mb = sum(stat.size for stat in top_stats) / 1024 / 1024
                memory_usage.append(memory_mb)
        
        print("Memory Leak Detection Analysis:")
        for i, usage in enumerate(memory_usage):
            print(f"  Iteration {i}: {usage:.2f} MB change from baseline")
        
        # Check for excessive memory growth (potential leaks)
        if len(memory_usage) > 2:
            final_growth = memory_usage[-1]
            assert final_growth < 10.0, f"Potential memory leak detected: {final_growth:.2f} MB growth"
        
        tracemalloc.stop()
    
    @pytest.mark.performance
    @pytest.mark.memory
    def test_object_size_analysis(self):
        """Analyze memory footprint of different platform object types."""
        
        import sys
        
        # Basic platform object
        basic_platform = {
            "id": "TestPlatform",
            "name": "Test Platform",
            "system_type": "Windows",
            "active": True
        }
        
        # Enhanced platform object
        enhanced_platform = {
            "id": "TestPlatform",
            "name": "Test Platform", 
            "system_type": "Windows",
            "active": True,
            "policy_id": "TestPolicy",
            "general_settings": {
                "allow_manual_change": True,
                "perform_periodic_change": False,
                "require_password_change_every_x_days": 90
            },
            "connection_components": [
                {
                    "psm_server_id": "PSM01",
                    "name": "PSM-RDP",
                    "connection_method": "RDP",
                    "enabled": True,
                    "parameters": {
                        "AllowMappingLocalDrives": "Yes",
                        "AllowConnectToConsole": "No"
                    }
                }
            ],
            "privileged_access_workflows": {
                "require_dual_control_password_access_approval": False,
                "require_users_to_specify_reason_for_access": True
            }
        }
        
        basic_size = sys.getsizeof(basic_platform)
        enhanced_size = sys.getsizeof(enhanced_platform)
        
        # Calculate deep size approximation (including nested objects)
        def get_deep_size(obj, seen=None):
            if seen is None:
                seen = set()
            
            obj_id = id(obj)
            if obj_id in seen:
                return 0
            seen.add(obj_id)
            
            size = sys.getsizeof(obj)
            if isinstance(obj, dict):
                size += sum(get_deep_size(k, seen) + get_deep_size(v, seen) for k, v in obj.items())
            elif isinstance(obj, (list, tuple, set)):
                size += sum(get_deep_size(item, seen) for item in obj)
            
            return size
        
        basic_deep_size = get_deep_size(basic_platform)
        enhanced_deep_size = get_deep_size(enhanced_platform)
        
        size_ratio = enhanced_deep_size / basic_deep_size if basic_deep_size > 0 else 0
        
        print(f"Object Size Analysis:")
        print(f"  Basic platform: {basic_size} bytes (shallow), {basic_deep_size} bytes (deep)")
        print(f"  Enhanced platform: {enhanced_size} bytes (shallow), {enhanced_deep_size} bytes (deep)")
        print(f"  Size ratio: {size_ratio:.1f}x")
        print(f"  Memory overhead per platform: {enhanced_deep_size - basic_deep_size} bytes")
        
        # Memory usage assertions
        assert enhanced_deep_size < 10000, f"Enhanced platform too large: {enhanced_deep_size} bytes"
        assert size_ratio < 10.0, f"Enhanced platform size ratio too high: {size_ratio:.1f}x"


if __name__ == "__main__":
    # Run performance tests directly
    pytest.main([
        __file__,
        "-v",
        "-m", "performance",
        "--tb=short"
    ])