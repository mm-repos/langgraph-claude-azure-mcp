"""MCP Server implementation for Azure AI Search."""

import asyncio
import logging
import sys
import time
from typing import Any, Dict, List, Optional


try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        GetPromptResult,
        Prompt,
        PromptArgument,
        PromptMessage,
        Resource,
        TextContent,
        Tool,
    )
    from pydantic import AnyUrl

    MCP_AVAILABLE = True
except ImportError:
    # Use stderr to avoid interfering with JSON-RPC stdout
    print(
        "MCP library not available. Please install with: pip install mcp",
        file=sys.stderr,
    )
    MCP_AVAILABLE = False

from langsmith import traceable

from .chain import AzureSearchChain
from .config import config
from .prompt_manager import PromptManager


# Set up logging to stderr to avoid interfering with JSON-RPC stdout
logging.basicConfig(
    level=getattr(logging, config.mcp_server.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


class AzureSearchMCPServer:
    """Azure AI Search MCP Server."""

    def __init__(self):
        """Initialize the MCP server."""
        self._init_warnings = []

        # Check configuration before initializing components
        self._check_configuration()

        # Initialize components (even if config is incomplete - they'll handle it gracefully)
        self.search_chain = AzureSearchChain()
        self.prompt_manager = PromptManager()

        if MCP_AVAILABLE:
            self.server = Server(config.mcp_server.name)
            self._setup_handlers()

    def _check_configuration(self):
        """Check and report configuration issues."""
        missing_azure = []
        if not config.azure_search.endpoint:
            missing_azure.append("AZURE_SEARCH_ENDPOINT")
        if not config.azure_search.api_key:
            missing_azure.append("AZURE_SEARCH_API_KEY")
        if not config.azure_search.index_name:
            missing_azure.append("AZURE_SEARCH_INDEX_NAME")

        if missing_azure:
            warning = f"Azure Search configuration incomplete. Missing: {', '.join(missing_azure)}. Search functionality will be disabled."
            self._init_warnings.append(warning)
            print(f"[CONFIG_WARNING] {warning}", file=sys.stderr)

        if not config.gemini.api_key:
            warning = "Gemini API key not found. LLM-based formatting will be disabled."
            self._init_warnings.append(warning)
            print(f"[CONFIG_WARNING] {warning}", file=sys.stderr)

    def _setup_handlers(self):
        """Set up MCP server handlers."""
        if not MCP_AVAILABLE:
            return

        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available resources."""

            resources = []

            # Add each tool as a resource
            tools = self._get_available_tools()
            for tool in tools:
                resources.append(
                    Resource(
                        uri=AnyUrl(f"tool://{tool.name}"),
                        name=tool.name,
                        description=tool.description,
                        mimeType="application/json",
                    )
                )

            # Add each prompt as a resource
            prompts = self._get_available_prompts()
            for prompt in prompts:
                resources.append(
                    Resource(
                        uri=AnyUrl(f"prompt://{prompt.name}"),
                        name=prompt.name,
                        description=prompt.description,
                        mimeType="text/plain",
                    )
                )

            return resources

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools."""
            return self._get_available_tools()

        @self.server.list_prompts()
        async def handle_list_prompts() -> List[Prompt]:
            """List available prompts."""
            return self._get_available_prompts()

        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: Dict[str, str]) -> GetPromptResult:
            """Get a specific prompt."""
            try:
                if arguments is None:
                    arguments = {}

                query = arguments.get("query", "")
                documents = arguments.get("documents", "")

                if name.startswith("format_"):
                    # Extract format type
                    format_type = name[7:]  # Remove "format_" prefix

                    # Get the prompt template for this format
                    template = self.prompt_manager.get_prompt_template_for_format(
                        format_type
                    )

                    # Format the prompt with the provided arguments
                    formatted_prompt = template.format_messages(
                        query=query, documents=documents
                    )

                    return GetPromptResult(
                        description=f"Format documents in {format_type} style",
                        messages=[
                            PromptMessage(
                                role="user",
                                content=TextContent(
                                    type="text",
                                    text=str(msg.content)
                                    if hasattr(msg, "content")
                                    else str(msg),
                                ),
                            )
                            for msg in formatted_prompt
                        ],
                    )

                elif name.startswith("persona_"):
                    # Extract persona type
                    persona_type = name[8:]  # Remove "persona_" prefix

                    # Get persona information
                    persona_info = self.prompt_manager.get_persona_info(persona_type)

                    # Create basic template
                    basic_template = f"""Acting as {persona_info["name"]}: {persona_info["description"]}

Please respond to the following query with the characteristics and expertise of {persona_info["name"]}:

<query>
{query}
</query>

**Response:**"""

                    return GetPromptResult(
                        description=f"Persona prompt for {persona_info['name']}",
                        messages=[
                            PromptMessage(
                                role="user",
                                content=TextContent(type="text", text=basic_template),
                            )
                        ],
                    )

                else:
                    error_text = f"Unknown prompt: {name}"
                    return GetPromptResult(
                        description="Error",
                        messages=[
                            PromptMessage(
                                role="user",
                                content=TextContent(type="text", text=error_text),
                            )
                        ],
                    )

            except Exception as e:
                logger.error(f"Error getting prompt {name}: {str(e)}")
                error_text = f"Error getting prompt: {str(e)}"
                return GetPromptResult(
                    description="Error",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(type="text", text=error_text),
                        )
                    ],
                )

        @self.server.call_tool()
        @traceable(name="mcp_tool_call")
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> List[TextContent]:
            """Handle tool calls."""
            import time

            start_time = time.time()

            # Add a timeout wrapper to prevent hanging
            async def _execute_tool():
                try:
                    if name == "search_documents":
                        # Check if configuration is valid before attempting search
                        if self._init_warnings:
                            warning_msg = (
                                "Search functionality is disabled due to configuration issues:\n"
                                + "\n".join(f"• {w}" for w in self._init_warnings)
                            )
                            return [
                                TextContent(
                                    type="text",
                                    text=f"❌ {warning_msg}\n\nPlease set the required environment variables and restart the server.",
                                )
                            ]

                        query = arguments["query"]
                        top_k = arguments.get("top_k", 5)
                        format_type = arguments.get("format_type", "structured")

                        search_result = await self.search_chain.run(
                            query, top_k=top_k, output_format=format_type
                        )

                        result = search_result["context"]
                        text_content = TextContent(type="text", text=result)
                        return [text_content]

                    elif name == "search_and_summarize":
                        # Check if configuration is valid before attempting search
                        if self._init_warnings:
                            warning_msg = (
                                "Search functionality is disabled due to configuration issues:\n"
                                + "\n".join(f"• {w}" for w in self._init_warnings)
                            )
                            return [
                                TextContent(
                                    type="text",
                                    text=f"❌ {warning_msg}\n\nPlease set the required environment variables and restart the server.",
                                )
                            ]

                        query = arguments["query"]
                        top_k = arguments.get("top_k", 5)

                        search_result = await self.search_chain.run(
                            query, top_k=top_k, output_format="summary"
                        )

                        result = search_result["context"]
                        return [TextContent(type="text", text=result)]

                    elif name == "search_with_analysis":
                        # Check if configuration is valid before attempting search
                        if self._init_warnings:
                            warning_msg = (
                                "Search functionality is disabled due to configuration issues:\n"
                                + "\n".join(f"• {w}" for w in self._init_warnings)
                            )
                            return [
                                TextContent(
                                    type="text",
                                    text=f"❌ {warning_msg}\n\nPlease set the required environment variables and restart the server.",
                                )
                            ]

                        query = arguments["query"]
                        top_k = arguments.get("top_k", 5)

                        search_result = await self.search_chain.run(
                            query, top_k=top_k, output_format="analysis"
                        )

                        result = search_result["context"]
                        return [TextContent(type="text", text=result)]

                    elif name == "get_document_context":
                        document_ids = arguments["document_ids"]

                        result = await self.search_chain.get_document_context_tool(
                            document_ids
                        )
                        return [TextContent(type="text", text=result)]

                    else:
                        error_msg = f"Unknown tool: {name}"
                        logger.error(error_msg)
                        return [TextContent(type="text", text=f"Error: {error_msg}")]

                except asyncio.CancelledError:
                    elapsed = time.time() - start_time
                    logger.warning(f"Tool call cancelled: {name} after {elapsed:.2f}s")
                    raise  # Re-raise to properly handle cancellation

                except Exception as e:
                    print(f"!!! EXCEPTION MESSAGE: {str(e)} !!!", file=sys.stderr)
                    logger.error(f"Critical error in tool {name}: {e}")
                    raise

            # Run with timeout
            try:
                return await asyncio.wait_for(_execute_tool(), timeout=30.0)
            except asyncio.TimeoutError:
                elapsed = time.time() - start_time
                logger.error(f"Tool call timeout: {name} after {elapsed:.2f}s")
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Tool call timed out after {elapsed:.2f}s. The search service may be experiencing delays.",
                    )
                ]
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Tool call error: {name} after {elapsed:.2f}s: {e}")
                return [
                    TextContent(type="text", text=f"Error: Tool call failed: {str(e)}")
                ]

    def _get_available_tools(self) -> List[Tool]:
        """Get list of available tools."""
        return [
            Tool(
                name="search_documents",
                description="Search for relevant documents in Azure AI Search with AI-enhanced analysis and formatting",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant documents",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of documents to return (default: 5)",
                            "default": 5,
                        },
                        "format_type": {
                            "type": "string",
                            "description": "Format type: 'summary' (AI-enhanced default), 'structured', or 'analysis'",
                            "enum": ["summary", "structured", "analysis"],
                            "default": "summary",
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="search_and_summarize",
                description="Search for documents and provide a concise summary of findings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant documents",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of documents to return (default: 5)",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="search_with_analysis",
                description="Search for documents and provide detailed relevance analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant documents",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of documents to return (default: 5)",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="get_document_context",
                description="Retrieve specific documents by their IDs for detailed context",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "document_ids": {
                            "type": "string",
                            "description": "Comma-separated list of document IDs to retrieve",
                        },
                        "format_output": {
                            "type": "boolean",
                            "description": "Whether to format the output for readability (default: true)",
                            "default": True,
                        },
                    },
                    "required": ["document_ids"],
                },
            ),
        ]

    def _get_available_prompts(self) -> List[Prompt]:
        """Get list of available prompts."""
        return [
            Prompt(
                name="search_query_optimization",
                description="Optimize search queries for better results",
                arguments=[
                    PromptArgument(
                        name="query",
                        description="The search query to optimize",
                        required=True,
                    )
                ],
            ),
            Prompt(
                name="document_analysis",
                description="Analyze document relevance and extract insights",
                arguments=[
                    PromptArgument(
                        name="documents",
                        description="Documents to analyze",
                        required=True,
                    ),
                    PromptArgument(
                        name="query",
                        description="The original search query",
                        required=True,
                    ),
                ],
            ),
        ]

    async def run_standalone_mode(self):
        """Run in standalone mode for testing without MCP."""
        logger.info("Running in standalone mode (MCP not available)")

        # Simple command-line interface for testing
        print("Azure AI Search Server - Standalone Mode")
        print("Available commands:")
        print("  search <query> - Search for documents (structured format)")
        print("  summary <query> - Search and provide summary")
        print("  analysis <query> - Search with relevance analysis")
        print("  get <doc_ids> - Get document context")
        print("  quit - Exit")

        while True:
            try:
                command = input("\n> ").strip()
                if not command:
                    continue

                if command.lower() in ["quit", "exit"]:
                    break

                parts = command.split(" ", 1)
                if len(parts) < 2:
                    print("Please provide a query or document IDs")
                    continue

                cmd, query = parts

                if cmd == "search":
                    search_result = await self.search_chain.run(
                        query, output_format="structured"
                    )
                    result = search_result["context"]
                    print(f"\nSearch Results:\n{result}")
                elif cmd == "summary":
                    search_result = await self.search_chain.run(
                        query, output_format="summary"
                    )
                    result = search_result["context"]
                    print(f"\nSummary:\n{result}")
                elif cmd == "analysis":
                    search_result = await self.search_chain.run(
                        query, output_format="analysis"
                    )
                    result = search_result["context"]
                    print(f"\nAnalysis:\n{result}")
                elif cmd == "get":
                    result = await self.search_chain.get_document_context_tool(query)
                    print(f"\nDocument Context:\n{result}")
                else:
                    print(
                        "Unknown command. Use 'search', 'summary', 'analysis', 'get', or 'quit'"
                    )

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

        await self.search_chain.close()

    async def run_mcp_mode(self):
        """Run in MCP mode."""
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP library not available")

        logger.info(f"Starting Azure AI Search MCP Server v{config.mcp_server.version}")

        try:
            # Use stdio transport
            from mcp.server.stdio import stdio_server

            async with stdio_server() as (read_stream, write_stream):
                from mcp.server import NotificationOptions
                from mcp.server.models import InitializationOptions

                initialization_options = InitializationOptions(
                    server_name=config.mcp_server.name,
                    server_version=config.mcp_server.version,
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                )

                await self.server.run(read_stream, write_stream, initialization_options)

        except asyncio.CancelledError:
            logger.info("Server run was cancelled")
            raise
        except Exception as e:
            import traceback
            print(f"[{time.strftime('%H:%M:%S')}] SERVER_TRACEBACK:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            logger.error(f"Server error: {str(e)}")
            raise
        finally:
            await self.search_chain.close()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Azure AI Search MCP Server")
    parser.add_argument(
        "--standalone", action="store_true", help="Run in standalone mode for testing"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    async def async_main():
        server = AzureSearchMCPServer()

        # Determine mode based on arguments
        if args.standalone or not MCP_AVAILABLE:
            # Standalone mode for testing
            logger.info("Running in standalone mode")
            await server.run_standalone_mode()
        else:
            # MCP mode (default)
            logger.info("Running in MCP mode (awaiting client connection)")
            await server.run_mcp_mode()

    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        raise


if __name__ == "__main__":
    main()
