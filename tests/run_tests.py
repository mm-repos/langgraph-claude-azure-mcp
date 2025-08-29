#!/usr/bin/env python3
"""
Run all essential tests for the Azure Search MCP Server.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def main():
    """Run all essential tests."""
    print("🧪 Running Azure Search MCP Server Tests\n")
    
    # Test 1: Environment Loading
    print("1️⃣ Testing Environment Configuration...")
    try:
        from test_env_loading import test_env_loading
        result = test_env_loading()
        if result:
            print("   ✅ Environment configuration test passed\n")
        else:
            print("   ❌ Environment configuration test failed\n")
    except Exception as e:
        print(f"   ❌ Environment test error: {e}\n")
    
    # Test 2: Integration Test
    print("2️⃣ Testing MCP Server Integration...")
    try:
        from test_integration import test_mcp_server
        result = await test_mcp_server()
        if result is not False:
            print("   ✅ Integration test passed\n")
        else:
            print("   ❌ Integration test failed\n")
    except Exception as e:
        print(f"   ❌ Integration test error: {e}\n")
    
    # Test 3: Chain Tests (using pytest)
    print("3️⃣ Testing Chain Functionality...")
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_chain.py", "-v"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("   ✅ Chain tests passed\n")
        else:
            print("   ❌ Chain tests failed\n")
            print(f"   Error: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Chain test error: {e}\n")
    
    # Test 4: Claude Setup Verification
    print("4️⃣ Verifying Claude Setup...")
    try:
        from verify_claude_setup import test_server_command
        test_server_command()
        print("   ✅ Claude setup verification completed\n")
    except Exception as e:
        print(f"   ❌ Claude setup error: {e}\n")
    
    print("🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
