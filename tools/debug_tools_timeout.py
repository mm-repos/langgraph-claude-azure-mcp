#!/usr/bin/env python3
"""Debug the tools list timeout issue."""

import asyncio
import json
import sys
import os
import subprocess
import time

async def debug_tools_list():
    """Debug the tools list timeout."""
    print("=== Debug Tools List Timeout ===")
    
    try:
        # Start the MCP server
        process = subprocess.Popen(
            ["azure-search-mcp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print("Started MCP server...")
        await asyncio.sleep(2)
        
        if process.poll() is None:
            print("✅ Server is running")
            
            # Send initialize
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "debug-client", "version": "1.0.0"}
                }
            }
            
            print("Sending initialize request...")
            if process.stdin:
                process.stdin.write(json.dumps(init_request) + "\n")
                process.stdin.flush()
                
                # Read stderr to see what's happening
                print("Checking stderr for messages...")
                
                # Non-blocking read of stderr
                import select
                import fcntl
                import os
                
                # Make stderr non-blocking on Windows (different approach)
                try:
                    # Try to read some stderr output
                    stderr_data = ""
                    start_time = time.time()
                    
                    while time.time() - start_time < 3:  # Wait 3 seconds
                        if process.stderr and process.stderr.readable():
                            # Read available data
                            try:
                                chunk = process.stderr.read(1024)
                                if chunk:
                                    stderr_data += chunk
                                    print(f"STDERR: {chunk.strip()}")
                            except:
                                pass
                        await asyncio.sleep(0.1)
                    
                    print(f"Collected stderr: {stderr_data[:500]}...")
                    
                    # Now try to read stdout
                    print("Attempting to read initialize response...")
                    if process.stdout:
                        try:
                            response = await asyncio.wait_for(
                                asyncio.create_task(asyncio.to_thread(process.stdout.readline)),
                                timeout=5.0
                            )
                            print(f"✅ Init response: {response.strip()[:100]}...")
                            
                            # Now try tools list
                            print("Sending tools list request...")
                            tools_request = {
                                "jsonrpc": "2.0",
                                "id": 2,
                                "method": "tools/list",
                                "params": {}
                            }
                            
                            process.stdin.write(json.dumps(tools_request) + "\n")
                            process.stdin.flush()
                            
                            print("Waiting for tools response (with stderr monitoring)...")
                            
                            # Monitor both stdout and stderr
                            start_time = time.time()
                            response_received = False
                            
                            while time.time() - start_time < 10 and not response_received:
                                # Check stderr
                                try:
                                    if process.stderr and process.stderr.readable():
                                        chunk = process.stderr.read(1024)
                                        if chunk:
                                            print(f"STDERR: {chunk.strip()}")
                                except:
                                    pass
                                
                                # Check stdout (non-blocking)
                                try:
                                    # This is a hack for non-blocking read
                                    tools_response = await asyncio.wait_for(
                                        asyncio.create_task(asyncio.to_thread(process.stdout.readline)),
                                        timeout=0.5
                                    )
                                    if tools_response.strip():
                                        print(f"✅ Tools response: {tools_response.strip()[:200]}...")
                                        response_received = True
                                        break
                                except asyncio.TimeoutError:
                                    pass  # Continue waiting
                                
                                await asyncio.sleep(0.1)
                            
                            if not response_received:
                                print("❌ No tools response received within 10 seconds")
                                print("This suggests the handler is hanging or not responding")
                                
                        except asyncio.TimeoutError:
                            print("❌ Timeout on initialize response")
                            
                except Exception as e:
                    print(f"Error monitoring stderr: {e}")
                    
        else:
            print(f"❌ Server exited: {process.returncode}")
        
        # Clean up
        if process.poll() is None:
            process.terminate()
            await asyncio.sleep(1)
            if process.poll() is None:
                process.kill()
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_tools_list())
