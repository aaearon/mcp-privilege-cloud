#!/usr/bin/env python3
"""
MCP Inspector CLI Testing Script for CyberArk Privilege Cloud MCP Server

This single-file script enables LLMs and developers to programmatically test 
the MCP server using the @modelcontextprotocol/inspector CLI mode.

Usage:
    # As a Python module
    from test_mcp_cli import MCPTester
    tester = MCPTester()
    result = tester.list_tools()
    
    # Command line
    python test_mcp_cli.py list_tools
    python test_mcp_cli.py call_tool list_accounts
    python test_mcp_cli.py health_check

Requirements:
    - Node.js and npm installed globally
    - @modelcontextprotocol/inspector package available globally (npm install -g @modelcontextprotocol/inspector)
    - Valid .env file with CyberArk credentials
    - uv package manager available
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class MCPTester:
    """
    Comprehensive MCP Inspector CLI wrapper for testing CyberArk Privilege Cloud MCP server.
    
    This class provides a simple interface for LLMs to test MCP server functionality
    through the @modelcontextprotocol/inspector CLI tool.
    """
    
    def __init__(self, timeout: int = 120, debug: bool = False):
        """
        Initialize the MCP tester.
        
        Args:
            timeout: Command timeout in seconds (default: 30)
            debug: Enable debug output (default: False)
        """
        self.timeout = timeout
        self.debug = debug
        self.project_root = self._find_project_root()
        self.env_vars = self._load_environment()
        
        # Validate required tools
        self._validate_requirements()
    
    def _find_project_root(self) -> Path:
        """Find the project root by looking for pyproject.toml."""
        current_dir = Path(__file__).parent.absolute()
        while not (current_dir / "pyproject.toml").exists():
            if current_dir == current_dir.parent:
                raise FileNotFoundError("Could not find project root (pyproject.toml not found)")
            current_dir = current_dir.parent
        return current_dir
    
    def _load_environment(self) -> Dict[str, str]:
        """Load environment variables from .env file and current environment."""
        env_vars = os.environ.copy()
        
        # Load .env file if it exists
        env_file = self.project_root / ".env"
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
                if self.debug:
                    print(f"✅ Loaded environment from {env_file}")
            except Exception as e:
                if self.debug:
                    print(f"⚠️ Warning: Could not load .env file: {e}")
        
        return env_vars
    
    def _validate_requirements(self) -> None:
        """Validate that required tools are available."""
        errors = []
        
        # Check Node.js
        try:
            subprocess.run(["node", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            errors.append("Node.js not found. Please install Node.js.")
        
        # Check npm
        try:
            subprocess.run(["npm", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            errors.append("npm not found. Please install npm.")
        
        # Check uv
        try:
            subprocess.run(["uv", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            errors.append("uv not found. Please install uv package manager.")
        
        # Check MCP inspector (using global installation)
        try:
            subprocess.run(["npx", "@modelcontextprotocol/inspector", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            errors.append("@modelcontextprotocol/inspector not found. Run: npm install -g @modelcontextprotocol/inspector")
        
        # Check for required environment variables
        required_env_vars = [
            "CYBERARK_CLIENT_ID",
            "CYBERARK_CLIENT_SECRET",
            "CYBERARK_IDENTITY_TENANT_ID",
            "CYBERARK_SUBDOMAIN"
        ]
        for var in required_env_vars:
            if var not in self.env_vars:
                errors.append(f"Missing required environment variable: {var}")
        
        if errors:
            raise RuntimeError("Validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    
    def _run_mcp_command(self, args: List[str]) -> Dict[str, Any]:
        """
        Execute MCP inspector CLI command and return parsed result.
        
        Args:
            args: Command arguments for the inspector CLI
            
        Returns:
            Parsed JSON response from the MCP server
            
        Raises:
            RuntimeError: If command execution fails
        """
        # Build the complete command using npx (which works correctly)
        command = [
            "npx", "@modelcontextprotocol/inspector",
            "--cli", "--",
            "uv", "run", "mcp-privilege-cloud"
        ] + args
        
        if self.debug:
            print(f"🔧 Executing: {' '.join(command)}")
            print(f"📁 Working directory: {self.project_root}")
        
        try:
            # Execute the command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.project_root,
                env=self.env_vars,
                timeout=self.timeout
            )
            
            if self.debug:
                print(f"📤 Raw stdout: {result.stdout}")
                if result.stderr:
                    print(f"⚠️ Stderr: {result.stderr}")
            
            # Parse JSON response
            output = result.stdout.strip()
            if not output:
                return {"success": False, "error": "No output received from command"}
            
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                # If not JSON, return as text
                return {"success": True, "data": output, "raw_output": True}
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {self.timeout} seconds",
                "suggestion": "Try increasing timeout or check server connectivity"
            }
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed with exit code {e.returncode}"
            if e.stderr:
                error_msg += f"\nStderr: {e.stderr}"
            if e.stdout:
                error_msg += f"\nStdout: {e.stdout}"
            
            return {
                "success": False,
                "error": error_msg,
                "suggestion": "Check server logs and credentials"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "suggestion": "Check system requirements and configuration"
            }
    
    def list_tools(self) -> Dict[str, Any]:
        """
        List all available MCP tools.
        
        Returns:
            Dictionary with success status and list of tools
            
        Example:
            >>> tester = MCPTester()
            >>> result = tester.list_tools()
            >>> if result["success"]:
            ...     print(f"Found {len(result['tools'])} tools")
        """
        result = self._run_mcp_command(["--method", "tools/list"])
        
        if result.get("success", True) and "tools" in result:
            return {
                "success": True,
                "tools": result["tools"],
                "tool_count": len(result["tools"]),
                "tool_names": [tool.get("name", "unknown") for tool in result["tools"]]
            }
        
        return result
    
    def list_resources(self) -> Dict[str, Any]:
        """
        List all available MCP resources.
        
        Returns:
            Dictionary with success status and list of resources
        """
        result = self._run_mcp_command(["--method", "resources/list"])
        
        if result.get("success", True) and "resources" in result:
            return {
                "success": True,
                "resources": result["resources"],
                "resource_count": len(result["resources"])
            }
        
        return result
    
    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Call a specific MCP tool with provided arguments.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool arguments as keyword arguments
            
        Returns:
            Dictionary with success status and tool result
            
        Example:
            >>> tester = MCPTester()
            >>> result = tester.call_tool("list_accounts", search="test")
            >>> if result["success"]:
            ...     print("Tool executed successfully")
        """
        args = ["--method", "tools/call", "--tool-name", tool_name]
        
        # Add tool arguments
        for key, value in kwargs.items():
            args.extend(["--tool-arg", f"{key}={value}"])
        
        result = self._run_mcp_command(args)
        
        # Enhance result with execution metadata
        if result.get("success", True):
            result["tool_name"] = tool_name
            result["arguments"] = kwargs
            result["execution_time"] = time.time()
        
        return result
    
    def test_server_health(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check of the MCP server.
        
        Returns:
            Dictionary with health check results including:
            - server_responsive: Whether server responds to commands
            - tools_available: Whether tools can be listed
            - sample_tool_works: Whether a sample tool can be executed
            - credential_status: Whether credentials appear to be working
        """
        health_report = {
            "timestamp": time.time(),
            "server_responsive": False,
            "tools_available": False,
            "sample_tool_works": False,
            "credential_status": "unknown",
            "issues": [],
            "recommendations": []
        }
        
        # Test 1: Check if server responds to tool listing
        tools_result = self.list_tools()
        if tools_result.get("success"):
            health_report["server_responsive"] = True
            health_report["tools_available"] = True
            health_report["tool_count"] = tools_result.get("tool_count", 0)
            
            if health_report["tool_count"] == 0:
                health_report["issues"].append("No tools found")
                health_report["recommendations"].append("Check server implementation")
        else:
            health_report["issues"].append(f"Tool listing failed: {tools_result.get('error', 'Unknown error')}")
            health_report["recommendations"].append("Check server startup and logs")
        
        # Test 2: Try to call a simple tool (list_accounts)
        if health_report["tools_available"]:
            sample_result = self.call_tool("list_accounts")
            if sample_result.get("success"):
                health_report["sample_tool_works"] = True
                health_report["credential_status"] = "working"
            else:
                error_msg = sample_result.get("error", "").lower()
                if "401" in error_msg or "unauthorized" in error_msg:
                    health_report["credential_status"] = "invalid"
                    health_report["issues"].append("Authentication failed")
                    health_report["recommendations"].append("Check .env credentials")
                elif "403" in error_msg or "forbidden" in error_msg:
                    health_report["credential_status"] = "insufficient_permissions"
                    health_report["issues"].append("Insufficient permissions")
                    health_report["recommendations"].append("Check user role in CyberArk")
                else:
                    health_report["issues"].append(f"Sample tool failed: {sample_result.get('error')}")
        
        # Overall health assessment
        health_report["overall_status"] = "healthy" if (
            health_report["server_responsive"] and 
            health_report["tools_available"] and 
            health_report["sample_tool_works"]
        ) else "unhealthy"
        
        return health_report
    
    def discover_tool_capabilities(self) -> Dict[str, Any]:
        """
        Discover all available tools and their capabilities.
        
        Returns:
            Dictionary with detailed tool information including parameters and descriptions
        """
        tools_result = self.list_tools()
        if not tools_result.get("success"):
            return tools_result
        
        capabilities = {
            "success": True,
            "discovery_time": time.time(),
            "total_tools": tools_result["tool_count"],
            "tools_by_category": {},
            "tool_details": {},
            "parameter_summary": {}
        }
        
        # Categorize tools by service
        for tool in tools_result["tools"]:
            tool_name = tool.get("name", "unknown")
            description = tool.get("description", "")
            input_schema = tool.get("inputSchema", {})
            
            # Determine category from tool name
            if tool_name.startswith("list_accounts") or "account" in tool_name.lower():
                category = "accounts"
            elif tool_name.startswith("list_safes") or "safe" in tool_name.lower():
                category = "safes"
            elif tool_name.startswith("list_platforms") or "platform" in tool_name.lower():
                category = "platforms"
            elif tool_name.startswith("list_applications") or "application" in tool_name.lower():
                category = "applications"
            else:
                category = "other"
            
            if category not in capabilities["tools_by_category"]:
                capabilities["tools_by_category"][category] = []
            
            capabilities["tools_by_category"][category].append(tool_name)
            capabilities["tool_details"][tool_name] = {
                "description": description,
                "input_schema": input_schema,
                "category": category
            }
            
            # Extract parameter info
            if input_schema and "properties" in input_schema:
                for param_name, param_info in input_schema["properties"].items():
                    if param_name not in capabilities["parameter_summary"]:
                        capabilities["parameter_summary"][param_name] = {
                            "type": param_info.get("type", "unknown"),
                            "used_in_tools": []
                        }
                    capabilities["parameter_summary"][param_name]["used_in_tools"].append(tool_name)
        
        return capabilities
    
    def run_basic_validation_suite(self) -> Dict[str, Any]:
        """
        Run a comprehensive validation suite testing core functionality.
        
        Returns:
            Dictionary with validation results for each test category
        """
        suite_results = {
            "timestamp": time.time(),
            "suite_status": "running",
            "tests_passed": 0,
            "tests_failed": 0,
            "test_results": {}
        }
        
        # Test categories to validate
        test_categories = [
            ("tool_discovery", "Tool Discovery", lambda: self.list_tools()),
            ("resource_discovery", "Resource Discovery", lambda: self.list_resources()),
            ("account_listing", "Account Listing", lambda: self.call_tool("list_accounts")),
            ("safe_listing", "Safe Listing", lambda: self.call_tool("list_safes")),
            ("platform_listing", "Platform Listing", lambda: self.call_tool("list_platforms")),
        ]
        
        # Run each test category
        for test_id, test_name, test_func in test_categories:
            try:
                result = test_func()
                success = result.get("success", False)
                
                suite_results["test_results"][test_id] = {
                    "name": test_name,
                    "success": success,
                    "result": result,
                    "timestamp": time.time()
                }
                
                if success:
                    suite_results["tests_passed"] += 1
                else:
                    suite_results["tests_failed"] += 1
                    
            except Exception as e:
                suite_results["test_results"][test_id] = {
                    "name": test_name,
                    "success": False,
                    "error": str(e),
                    "timestamp": time.time()
                }
                suite_results["tests_failed"] += 1
        
        # Calculate overall status
        total_tests = suite_results["tests_passed"] + suite_results["tests_failed"]
        success_rate = (suite_results["tests_passed"] / total_tests * 100) if total_tests > 0 else 0
        
        suite_results["suite_status"] = "completed"
        suite_results["success_rate"] = success_rate
        suite_results["overall_success"] = success_rate >= 80  # 80% threshold
        
        return suite_results
    
    def generate_test_report(self) -> str:
        """
        Generate a comprehensive test report in human-readable format.
        
        Returns:
            Formatted test report as a string
        """
        print("🔍 Generating comprehensive MCP server test report...")
        
        # Run all tests
        health = self.test_server_health()
        capabilities = self.discover_tool_capabilities()
        validation = self.run_basic_validation_suite()
        
        # Build report
        report_lines = [
            "=" * 60,
            "CyberArk Privilege Cloud MCP Server Test Report",
            "=" * 60,
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "🏥 HEALTH CHECK",
            "-" * 20,
            f"Overall Status: {'✅ HEALTHY' if health['overall_status'] == 'healthy' else '❌ UNHEALTHY'}",
            f"Server Responsive: {'✅' if health['server_responsive'] else '❌'}",
            f"Tools Available: {'✅' if health['tools_available'] else '❌'}",
            f"Sample Tool Works: {'✅' if health['sample_tool_works'] else '❌'}",
            f"Credential Status: {health['credential_status'].upper()}",
        ]
        
        if health['issues']:
            report_lines.extend([
                "",
                "⚠️ ISSUES FOUND:",
                *[f"  - {issue}" for issue in health['issues']],
                "",
                "💡 RECOMMENDATIONS:",
                *[f"  - {rec}" for rec in health['recommendations']]
            ])
        
        if capabilities.get("success"):
            report_lines.extend([
                "",
                "🔧 TOOL CAPABILITIES",
                "-" * 20,
                f"Total Tools: {capabilities['total_tools']}",
                ""
            ])
            
            for category, tools in capabilities["tools_by_category"].items():
                report_lines.append(f"📁 {category.upper()}: {len(tools)} tools")
                for tool in tools[:5]:  # Show first 5 tools per category
                    report_lines.append(f"  - {tool}")
                if len(tools) > 5:
                    report_lines.append(f"  ... and {len(tools) - 5} more")
                report_lines.append("")
        
        if validation.get("suite_status") == "completed":
            report_lines.extend([
                "✅ VALIDATION SUITE",
                "-" * 20,
                f"Tests Passed: {validation['tests_passed']}",
                f"Tests Failed: {validation['tests_failed']}",
                f"Success Rate: {validation['success_rate']:.1f}%",
                f"Overall: {'✅ PASS' if validation['overall_success'] else '❌ FAIL'}",
                ""
            ])
            
            for test_id, test_info in validation["test_results"].items():
                status = "✅" if test_info["success"] else "❌"
                report_lines.append(f"  {status} {test_info['name']}")
        
        report_lines.extend([
            "",
            "=" * 60,
            "End of Report"
        ])
        
        return "\n".join(report_lines)


def main():
    """Command-line interface for the MCP tester."""
    if len(sys.argv) < 2:
        print("Usage: python test_mcp_cli.py <command> [args...]")
        print("\nAvailable commands:")
        print("  list_tools          - List all available tools")
        print("  list_resources      - List all available resources")
        print("  call_tool <name>    - Call a specific tool")
        print("  health_check        - Run server health check")
        print("  capabilities        - Discover tool capabilities")
        print("  validation_suite    - Run comprehensive validation")
        print("  generate_report     - Generate full test report")
        print("\nExample:")
        print("  python test_mcp_cli.py list_tools")
        print("  python test_mcp_cli.py call_tool list_accounts")
        sys.exit(1)
    
    command = sys.argv[1]
    tester = MCPTester(debug=True)
    
    try:
        if command == "list_tools":
            result = tester.list_tools()
            print(json.dumps(result, indent=2))
            
        elif command == "list_resources":
            result = tester.list_resources()
            print(json.dumps(result, indent=2))
            
        elif command == "call_tool":
            if len(sys.argv) < 3:
                print("Error: call_tool requires a tool name")
                sys.exit(1)
            tool_name = sys.argv[2]
            
            # Parse additional arguments as key=value pairs
            kwargs = {}
            for arg in sys.argv[3:]:
                if "=" in arg:
                    key, value = arg.split("=", 1)
                    kwargs[key] = value
            
            result = tester.call_tool(tool_name, **kwargs)
            print(json.dumps(result, indent=2))
            
        elif command == "health_check":
            result = tester.test_server_health()
            print(json.dumps(result, indent=2))
            
        elif command == "capabilities":
            result = tester.discover_tool_capabilities()
            print(json.dumps(result, indent=2))
            
        elif command == "validation_suite":
            result = tester.run_basic_validation_suite()
            print(json.dumps(result, indent=2))
            
        elif command == "generate_report":
            report = tester.generate_test_report()
            print(report)
            
        else:
            print(f"Error: Unknown command '{command}'")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
