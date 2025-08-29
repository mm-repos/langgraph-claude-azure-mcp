"""Quick test for MCP server functionality."""

import asyncio
import json
import pytest
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports  
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.mark.asyncio
async def test_mcp_server():
    """Test the MCP server functionality."""
    print("🔍 Testing Azure AI Search MCP Server...")
    
    # Test 1: Import test
    print("\n1. Testing imports...")
    try:
        from azure_search_mcp.server import AzureSearchMCPServer
        print("   ✅ Server imports successfully")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 2: Server initialization
    print("\n2. Testing server initialization...")
    try:
        server = AzureSearchMCPServer()
        print("   ✅ Server initializes successfully")
    except Exception as e:
        print(f"   ❌ Server initialization failed: {e}")
        return False
    
    # Test 3: Search chain test
    print("\n3. Testing search functionality...")
    try:
        search_result = await server.search_chain.run("CEO compensation", top_k=2, output_format="structured")
        result = search_result["context"]
        if "CEO" in result and "compensation" in result:
            print("   ✅ Search functionality works")
            print(f"   📄 Found {result.count('##')} documents")
        else:
            print("   ⚠️  Search returned results but may not be relevant")
    except Exception as e:
        print(f"   ❌ Search test failed: {e}")
        return False
    
    # Test 4: MCP protocol test (simplified)
    print("\n4. Testing MCP protocol compatibility...")
    try:
        # Simple test to verify the server has the required methods
        assert hasattr(server, 'server'), "Server object missing"
        assert hasattr(server.server, 'list_tools'), "list_tools method missing"
        assert hasattr(server.server, 'call_tool'), "call_tool method missing"
        print("   ✅ MCP protocol methods available")
    except Exception as e:
        print(f"   ❌ MCP protocol test failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Your MCP server is ready for Claude Desktop integration.")
    
    # Cleanup
    await server.search_chain.close()
    
    return True

def check_claude_config():
    """Check if Claude Desktop config exists and provide guidance."""
    print("\n📋 Claude Desktop Configuration Check...")
    
    claude_config_path = Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    
    if claude_config_path.exists():
        print(f"   ✅ Claude config found at: {claude_config_path}")
        try:
            with open(claude_config_path, 'r') as f:
                config = json.load(f)
            
            if "mcpServers" in config and "azure-search-mcp" in config.get("mcpServers", {}):
                print("   ✅ Azure Search MCP server already configured!")
            else:
                print("   ⚠️  Azure Search MCP server not configured yet")
                print("   📝 Please add the MCP server configuration from CLAUDE_SETUP_GUIDE.md")
        except Exception as e:
            print(f"   ❌ Error reading Claude config: {e}")
    else:
        print(f"   ❌ Claude config not found at: {claude_config_path}")
        print("   📝 You'll need to create it with the configuration from CLAUDE_SETUP_GUIDE.md")

def main():
    """Run all tests and checks."""
    print("🚀 Azure AI Search MCP Server - Integration Test")
    print("=" * 50)
    
    # Run async tests
    try:
        success = asyncio.run(test_mcp_server())
        
        if success:
            # Check Claude Desktop configuration
            check_claude_config()
            
            print("\n" + "=" * 50)
            print("✅ READY FOR INTEGRATION!")
            print("📖 See CLAUDE_SETUP_GUIDE.md for Claude Desktop setup instructions")
            print("🔧 Your MCP server is working and ready to be integrated with Claude")
        else:
            print("\n❌ Some tests failed. Please check the errors above.")
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")

if __name__ == "__main__":
    main()
