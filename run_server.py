#!/usr/bin/env python3
"""
CyberArk Privilege Cloud MCP Server Entry Point

Multiplatform entry point for running the CyberArk MCP Server.
Automatically handles platform-specific configurations for Windows and Unix systems.
"""

import os
import sys
import io
import platform

# Platform-specific setup for Windows UTF-8 encoding
if sys.platform == "win32" or platform.system() == "Windows":
    try:
        # Reconfigure stdout/stderr to use UTF-8 encoding
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        
        # Set console code page to UTF-8
        import subprocess
        subprocess.run(['chcp', '65001'], capture_output=True, check=False)
    except Exception as e:
        # Fallback - continue without UTF-8 setup
        print(f"[WARN] UTF-8 setup failed: {e}")

# Add src directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

def main():
    """Main entry point with multiplatform support"""
    
    # Deprecation warning for legacy entry point
    print("=" * 80)
    print("⚠️  DEPRECATION WARNING: run_server.py is deprecated")
    print("=" * 80)
    print("This entry point is maintained for backward compatibility but is deprecated.")
    print("Please migrate to one of the following standardized methods:")
    print()
    print("📦 Primary (recommended):")
    print("   uvx mcp-privilege-cloud")
    print()
    print("🔧 Development:")
    print("   uv run mcp-privilege-cloud")
    print()
    print("🐍 Fallback:")
    print("   python -m mcp_privilege_cloud")
    print()
    print("These methods provide better dependency management and standardized execution.")
    print("=" * 80)
    print()
    
    # Load .env file if it exists
    env_file = os.path.join(project_root, '.env')
    if os.path.exists(env_file):
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print(f"[OK] Loaded environment from {env_file}")
        except ImportError:
            # Manual .env loading if python-dotenv not available
            encoding = 'utf-8' if sys.platform != "win32" else 'utf-8'
            try:
                with open(env_file, encoding=encoding) as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            key, value = line.strip().split('=', 1)
                            if key and value:
                                os.environ[key] = value
                print(f"[OK] Manually loaded environment from {env_file}")
            except UnicodeDecodeError:
                # Fallback for encoding issues
                with open(env_file, encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            key, value = line.strip().split('=', 1)
                            if key and value:
                                os.environ[key] = value
                print(f"[OK] Loaded environment from {env_file} (with encoding fallback)")
    else:
        print("[WARN] No .env file found - using system environment variables")
    
    # Platform-specific instructions
    venv_activation = "venv\\Scripts\\activate" if sys.platform == "win32" else "source venv/bin/activate"
    
    try:
        # Import the main function from the MCP server module
        from mcp_privilege_cloud.mcp_server import main as server_main
        
        print(f"[INFO] Starting CyberArk Privilege Cloud MCP Server on {platform.system()}...")
        server_main()
        
    except ImportError as e:
        print(f"[ERROR] Import Error: {e}")
        print("\n[TROUBLESHOOTING]")
        print("1. Ensure you're in the project root directory")
        print(f"2. Activate virtual environment: {venv_activation}")
        print("3. Install dependencies: pip install -r requirements.txt")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Server stopped by user (Ctrl+C)")
        
    except Exception as e:
        print(f"\n[ERROR] Server error: {e}")
        print("\n[TROUBLESHOOTING] Check your configuration:")
        print("1. Verify environment variables in .env file")
        print("2. Check CyberArk service account permissions")
        print("3. Ensure network connectivity to CyberArk")
        print(f"4. Platform: {platform.system()} {platform.release()}")
        sys.exit(1)

if __name__ == "__main__":
    main()