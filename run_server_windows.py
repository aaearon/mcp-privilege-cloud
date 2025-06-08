#!/usr/bin/env python3
"""
CyberArk Privilege Cloud MCP Server Entry Point for Windows

Windows-compatible version with proper encoding handling.
"""

import os
import sys
import io

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    # Reconfigure stdout/stderr to use UTF-8 encoding
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    # Set console code page to UTF-8
    try:
        import subprocess
        subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
    except:
        pass

# Add src directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

def main():
    """Main entry point"""
    # Load .env file if it exists
    env_file = os.path.join(project_root, '.env')
    if os.path.exists(env_file):
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print(f"[OK] Loaded environment from {env_file}")
        except ImportError:
            # Manual .env loading if python-dotenv not available
            with open(env_file, encoding='utf-8') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key and value:
                            os.environ[key] = value
            print(f"[OK] Manually loaded environment from {env_file}")
    else:
        print("[WARN] No .env file found - using system environment variables")
    
    try:
        # Import the main function from the MCP server module
        from cyberark_mcp.mcp_server import main as server_main
        
        print("[INFO] Starting CyberArk Privilege Cloud MCP Server...")
        server_main()
        
    except ImportError as e:
        print(f"[ERROR] Import Error: {e}")
        print("\n[TROUBLESHOOTING]")
        print("1. Ensure you're in the project root directory")
        print("2. Activate virtual environment: venv\\Scripts\\activate")
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
        sys.exit(1)

if __name__ == "__main__":
    main()