#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strike7 MCP Capability Test
Run this to check if your environment can support an MCP server.

Usage:
    python test_mcp_capability.py
"""

import sys
import subprocess
import json
import os

# Fix encoding for Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

def check_python_version():
    """Check Python version >= 3.10"""
    print("1. Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} (need 3.10+)")
        return False

def check_mcp_sdk():
    """Check if MCP SDK can be imported"""
    print("2. Checking MCP SDK...")
    try:
        import mcp
        print(f"   ✅ MCP SDK installed (version: {getattr(mcp, '__version__', 'unknown')})")
        return True
    except ImportError:
        print("   ❌ MCP SDK not installed")
        print("      Run: pip install mcp --break-system-packages")
        return False

def check_fastmcp():
    """Check FastMCP availability"""
    print("3. Checking FastMCP...")
    try:
        from mcp.server.fastmcp import FastMCP
        print("   ✅ FastMCP available")
        return True
    except ImportError as e:
        print(f"   ⚠️  FastMCP not available: {e}")
        print("      May need: pip install 'mcp[server]' --break-system-packages")
        return False

def check_docker():
    """Check Docker availability"""
    print("4. Checking Docker...")
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("   ✅ Docker is running")
            return True
        else:
            print(f"   ❌ Docker error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("   ❌ Docker not found")
        return False
    except subprocess.TimeoutExpired:
        print("   ❌ Docker timeout")
        return False

def check_strike7_api():
    """Check Strike7 Dashboard API"""
    print("5. Checking Strike7 Dashboard API...")
    try:
        import requests
        response = requests.get("http://localhost:5500/api/benchmarks", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Strike7 API responding ({len(data)} benchmarks)")
            return True
        else:
            print(f"   ❌ Strike7 API returned {response.status_code}")
            return False
    except ImportError:
        print("   ⚠️  requests module not installed")
        print("      Run: pip install requests --break-system-packages")
        return False
    except Exception as e:
        print(f"   ❌ Strike7 API not reachable: {e}")
        print("      Is the dashboard running? (cd dashboard && python app.py)")
        return False

def check_async_support():
    """Check asyncio support"""
    print("6. Checking async support...")
    try:
        import asyncio
        async def test():
            return True
        result = asyncio.run(test())
        print("   ✅ Asyncio working")
        return True
    except Exception as e:
        print(f"   ❌ Asyncio error: {e}")
        return False

def check_requests():
    """Check requests library"""
    print("7. Checking requests library...")
    try:
        import requests
        print("   ✅ Requests library available")
        return True
    except ImportError:
        print("   ❌ Requests not installed")
        print("      Run: pip install requests --break-system-packages")
        return False

def test_minimal_mcp_server():
    """Test creating a minimal MCP server"""
    print("8. Testing minimal MCP server creation...")
    try:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test-server")

        @mcp.tool()
        def test_tool(message: str) -> str:
            """A test tool"""
            return f"Received: {message}"

        print("   ✅ MCP server created with tool")
        return True
    except Exception as e:
        print(f"   ❌ MCP server creation failed: {e}")
        return False

def main():
    """Run all capability checks"""
    print("=" * 60)
    print("Strike7 MCP Server Capability Check")
    print("=" * 60)
    print()

    results = {
        "Python 3.10+": check_python_version(),
        "MCP SDK": check_mcp_sdk(),
        "FastMCP": check_fastmcp(),
        "Docker": check_docker(),
        "Strike7 API": check_strike7_api(),
        "Async Support": check_async_support(),
        "Requests Library": check_requests(),
    }

    # Only test MCP server if SDK is available
    if results["MCP SDK"] and results["FastMCP"]:
        results["MCP Server Test"] = test_minimal_mcp_server()
    else:
        results["MCP Server Test"] = False

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check, result in results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}")

    print()
    print(f"Result: {passed}/{total} checks passed")

    # Determine overall status
    critical_checks = ["Python 3.10+", "Docker", "Async Support"]
    critical_passed = all(results.get(c, False) for c in critical_checks)

    if passed >= 6 and critical_passed:
        print("\n🎉 Your environment CAN support an MCP server!")
        print("   Proceed with MCP implementation.")
        status = "READY"
    elif passed >= 4:
        print("\n⚠️  Your environment PARTIALLY supports MCP.")
        print("   Fix the failing checks before proceeding:")
        for check, result in results.items():
            if not result:
                print(f"   - {check}")
        status = "PARTIAL"
    else:
        print("\n❌ Your environment needs setup before MCP.")
        print("   Address the failing checks first.")
        status = "NOT_READY"

    # Installation commands for missing components
    print()
    print("=" * 60)
    print("INSTALLATION COMMANDS (if needed)")
    print("=" * 60)

    if not results.get("MCP SDK", True):
        print("  pip install mcp --break-system-packages")
    if not results.get("FastMCP", True):
        print("  pip install 'mcp[server]' --break-system-packages")
    if not results.get("Requests Library", True):
        print("  pip install requests --break-system-packages")
    if not results.get("Strike7 API", True):
        print("  # Start Strike7 dashboard:")
        print("  cd dashboard && python app.py")

    return status == "READY"

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
