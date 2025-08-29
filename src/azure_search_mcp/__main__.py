#!/usr/bin/env python3
"""Entry point for the Azure AI Search MCP Server."""

import sys


def main():
    """Main entry point."""
    try:
        from azure_search_mcp.server import main as server_main

        server_main()
    except KeyboardInterrupt:
        print("\nShutting down server...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
