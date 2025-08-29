#!/usr/bin/env python3
"""Test reading API keys from .env file."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_env_loading():
    """Test that environment variables are loaded from .env file."""
    print("=== Testing .env File Loading ===")
    
    try:
        from azure_search_mcp.config import config
        
        print("\n--- Azure Search Configuration ---")
        print(f"Endpoint: {config.azure_search.endpoint}")
        print(f"API Key: {'*' * len(config.azure_search.api_key) if config.azure_search.api_key else 'NOT SET'}")
        print(f"Index Name: {config.azure_search.index_name}")
        
        print("\n--- Google Gemini Configuration ---")
        print(f"API Key: {'*' * len(config.gemini.api_key) if config.gemini.api_key else 'NOT SET'}")
        print(f"Model: {config.gemini.model_name}")
        print(f"Temperature: {config.gemini.temperature}")
        
        print("\n--- LangSmith Configuration ---")
        print(f"Tracing Enabled: {config.langsmith.tracing_enabled}")
        print(f"API Key: {'*' * len(config.langsmith.api_key) if config.langsmith.api_key else 'NOT SET'}")
        print(f"Project: {config.langsmith.project}")
        
        # Check if all required keys are present
        missing_keys = []
        if not config.azure_search.endpoint:
            missing_keys.append("AZURE_SEARCH_ENDPOINT")
        if not config.azure_search.api_key:
            missing_keys.append("AZURE_SEARCH_API_KEY")
        if not config.azure_search.index_name:
            missing_keys.append("AZURE_SEARCH_INDEX_NAME")
        if not config.gemini.api_key:
            missing_keys.append("GOOGLE_API_KEY")
        
        if missing_keys:
            print(f"\n❌ Missing required keys: {', '.join(missing_keys)}")
            return False
        else:
            print(f"\n✅ All required API keys loaded successfully from .env file!")
            return True
            
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_env_loading()
    sys.exit(0 if success else 1)
