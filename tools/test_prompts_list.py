#!/usr/bin/env python3
"""
Test script to verify that the prompts/list method is now working.
This test will connect to the MCP server and call the prompts/list method.
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Any, Dict

async def test_prompts_list():
    """Test the prompts/list method specifically."""
    print("🧪 Testing prompts/list method...")
    
    # Start the MCP server process
    cmd = [
        "conda", "run", "-n", "base", "--no-capture-output",
        "python", "-m", "azure_search_mcp"
    ]
    
    print(f"Starting MCP server: {' '.join(cmd)}")
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd="..\\Documents\\RAG\\MCP-POC"
    )
    
    try:
        # Wait for server to initialize
        await asyncio.sleep(2)
        
        # Ensure stdin and stdout are available
        if not process.stdin or not process.stdout:
            print("❌ Failed to establish stdin/stdout with server")
            return False
        
        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "prompts": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("📤 Sending initialize request...")
        process.stdin.write((json.dumps(init_request) + "\n").encode())
        await process.stdin.drain()
        
        # Read initialization response
        response_line = await asyncio.wait_for(process.stdout.readline(), timeout=5.0)
        response = json.loads(response_line.decode())
        print(f"📥 Init response: {response}")
        
        if "error" in response:
            print(f"❌ Initialization failed: {response['error']}")
            return False
        
        # Send prompts/list request
        prompts_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "prompts/list",
            "params": {}
        }
        
        print("📤 Sending prompts/list request...")
        process.stdin.write((json.dumps(prompts_request) + "\n").encode())
        await process.stdin.drain()
        
        # Read prompts/list response
        response_line = await asyncio.wait_for(process.stdout.readline(), timeout=5.0)
        response = json.loads(response_line.decode())
        print(f"📥 Prompts response: {response}")
        
        if "error" in response:
            print(f"❌ prompts/list failed: {response['error']}")
            return False
        
        if "result" in response and "prompts" in response["result"]:
            prompts = response["result"]["prompts"]
            print(f"✅ SUCCESS! Found {len(prompts)} prompts:")
            for prompt in prompts:
                print(f"   • {prompt['name']}: {prompt['description']}")
            return True
        else:
            print("❌ Unexpected response format")
            return False
            
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for response")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Clean up
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=3.0)
        except asyncio.TimeoutError:
            process.kill()

async def main():
    """Main test function."""
    print("🔧 MCP Prompts/List Test")
    print("=" * 50)
    
    success = await test_prompts_list()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ prompts/list method is working correctly!")
        print("🎉 The 'Method not found' error should be fixed.")
    else:
        print("❌ prompts/list method is still not working.")
        print("🔍 Check the server logs for more details.")

if __name__ == "__main__":
    asyncio.run(main())
