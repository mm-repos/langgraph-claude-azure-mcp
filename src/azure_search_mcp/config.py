"""Configuration management for Azure AI Search MCP Server."""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Load environment variables from .env file
load_dotenv()


class AzureSearchConfig(BaseModel):
    """Configuration for Azure AI Search."""

    endpoint: str = Field(
        default_factory=lambda: os.getenv("AZURE_SEARCH_ENDPOINT", "")
    )
    api_key: str = Field(default_factory=lambda: os.getenv("AZURE_SEARCH_API_KEY", ""))
    index_name: str = Field(
        default_factory=lambda: os.getenv("AZURE_SEARCH_INDEX_NAME", "")
    )


class MCPServerConfig(BaseModel):
    """Configuration for MCP Server."""

    name: str = Field(
        default_factory=lambda: os.getenv("MCP_SERVER_NAME", "azure-search-mcp")
    )
    version: str = Field(
        default_factory=lambda: os.getenv("MCP_SERVER_VERSION", "0.1.0")
    )
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


class LangSmithConfig(BaseModel):
    """Configuration for LangSmith tracing."""

    tracing_enabled: bool = Field(
        default_factory=lambda: os.getenv("LANGCHAIN_TRACING_V2", "false").lower()
        == "true"
    )
    endpoint: str = Field(
        default_factory=lambda: os.getenv(
            "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
        )
    )
    api_key: str = Field(default_factory=lambda: os.getenv("LANGCHAIN_API_KEY", ""))
    project: str = Field(
        default_factory=lambda: os.getenv("LANGCHAIN_PROJECT", "azure-search-mcp")
    )


class GeminiConfig(BaseModel):
    """Configuration for Google Gemini."""

    api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    model_name: str = Field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    )
    temperature: float = Field(
        default_factory=lambda: float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
    )


class Config:
    """Main configuration class."""

    def __init__(self):
        self.azure_search = AzureSearchConfig()
        self.mcp_server = MCPServerConfig()
        self.langsmith = LangSmithConfig()
        self.gemini = GeminiConfig()

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls()


# Global configuration instance
config = Config.from_env()
