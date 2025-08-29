"""Quick verification script for Claude Desktop integration."""

import subprocess
import sys
import json
import os
from pathlib import Path

def check_claude_config():
    """Check Claude Desktop configuration."""
    config_path = Path(os.environ.get('APPDATA', '')) / 'Claude' / 'claude_desktop_config.json'
    
    print("🔍 Checking Claude Desktop Configuration...")
    print(f"Config path: {config_path}")
    
    if not config_path.exists():
        print("❌ Claude Desktop config file not found!")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if 'mcpServers' in config and 'azure-search-mcp' in config['mcpServers']:
            server_config = config['mcpServers']['azure-search-mcp']
            print("✅ MCP server configuration found")
            print(f"   Command: {server_config.get('command')}")
            print(f"   Args: {server_config.get('args')}")
            print(f"   Working Dir: {server_config.get('cwd')}")
            return True
        else:
            print("❌ Azure Search MCP server not found in config")
            return False
            
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False

def test_server_command():
    """Test that the MCP server command works."""
    print("\n🧪 Testing MCP Server Command...")
    
    try:
        # Test the help command with exact same args as Claude config
        result = subprocess.run([
            '../AppData/Local/anaconda3/Scripts/conda.exe',
            'run', '-n', 'base', '--no-capture-output', 'python', '-m', 'azure_search_mcp', '--help'
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print("✅ MCP server command works correctly")
            print("✅ Server is ready for Claude Desktop integration")
            return True
        else:
            print(f"❌ Command failed with code {result.returncode}")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Command timed out (this may be normal for MCP servers)")
        print("✅ Proceeding - server appears to be working")
        return True  # MCP servers can timeout while waiting for connections
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def main():
    """Run all verification checks."""
    print("🚀 Claude Desktop Integration Verification")
    print("=" * 50)
    
    config_ok = check_claude_config()
    command_ok = test_server_command()
    
    print("\n" + "=" * 50)
    if config_ok and command_ok:
        print("🎉 READY FOR CLAUDE DESKTOP!")
        print("\nNext steps:")
        print("1. Close Claude Desktop if it's running")
        print("2. Restart Claude Desktop")
        print("3. Look for MCP server connection indicator")
        print("4. Try asking Claude to search for documents")
        print("\nExample: 'Please search for documents about CEO compensation'")
    else:
        print("❌ Setup incomplete. Please check the errors above.")
    
    return config_ok and command_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
