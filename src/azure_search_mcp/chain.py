"""LangGraph chain implementation for Azure AI Search integration."""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langsmith import traceable

# Assuming these are in the same directory
from .azure_search import AzureSearchClient
from .config import config
from .prompt_manager import PromptManager


logger = logging.getLogger(__name__)


class SearchState(TypedDict):
    """State for the search chain."""

    query: str
    search_type: str  # "text", "hybrid"
    top_k: int
    output_format: str  # "summary", "analysis", "structured"
    documents: List[Dict[str, Any]]
    context: str  # This will hold the FINAL output of any chain
    raw_context: str  # Holds the unprocessed context from documents
    metadata: Dict[str, Any]
    error: Optional[str]


class AzureSearchChain:
    """LangGraph chain for Azure AI Search operations."""

    def __init__(self):
        """Initialize the search chain."""
        # Configure LangSmith tracing if enabled
        if config.langsmith.tracing_enabled and config.langsmith.api_key:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_ENDPOINT"] = config.langsmith.endpoint
            os.environ["LANGCHAIN_API_KEY"] = config.langsmith.api_key
            os.environ["LANGCHAIN_PROJECT"] = config.langsmith.project

        self.search_client = AzureSearchClient()

        # Initialize prompt manager
        self.prompt_manager = PromptManager()

        # Initialize Google Gemini LLM
        if config.gemini.api_key:
            self.llm = ChatGoogleGenerativeAI(
                model=config.gemini.model_name,
                google_api_key=config.gemini.api_key,
                temperature=config.gemini.temperature,
            )
        else:
            logger.warning("Gemini API key not found. LLM will not be available.")
            self.llm = None

        # --- PROMPT TEMPLATES FROM JSON CONFIGURATION ---

        # Load prompt templates from PromptManager
        self.structured_formatter_prompt = (
            self.prompt_manager.get_prompt_template_for_format("structured")
        )
        self.context_summarizer_prompt = (
            self.prompt_manager.get_prompt_template_for_format("summary")
        )
        self.relevance_analyzer_prompt = (
            self.prompt_manager.get_prompt_template_for_format("analysis")
        )

        # --- Build LCEL Chains from Prompts ---
        if self.llm:
            self.structured_formatter_chain = (
                RunnableLambda(self._log_prompt_input).with_config(
                    {"run_name": "ChatPromptTemplate_StructuredFormatter_Input"}
                )
                | self.structured_formatter_prompt.with_config(
                    {"run_name": "ChatPromptTemplate_StructuredFormatter"}
                )
                | RunnableLambda(self._log_full_prompt).with_config(
                    {"run_name": "FULL_PROMPT_StructuredFormatter"}
                )
                | self.llm.with_config({"run_name": "Gemini_StructuredFormatter"})
                | StrOutputParser().with_config(
                    {"run_name": "StructuredFormatter_Output"}
                )
            )
            self.context_summarizer_chain = (
                RunnableLambda(self._log_prompt_input).with_config(
                    {"run_name": "ChatPromptTemplate_ContextSummarizer_Input"}
                )
                | self.context_summarizer_prompt.with_config(
                    {"run_name": "ChatPromptTemplate_ContextSummarizer"}
                )
                | RunnableLambda(self._log_full_prompt).with_config(
                    {"run_name": "FULL_PROMPT_ContextSummarizer"}
                )
                | self.llm.with_config({"run_name": "Gemini_ContextSummarizer"})
                | StrOutputParser().with_config(
                    {"run_name": "ContextSummarizer_Output"}
                )
            )
            self.relevance_analyzer_chain = (
                RunnableLambda(self._log_prompt_input).with_config(
                    {"run_name": "ChatPromptTemplate_RelevanceAnalyzer_Input"}
                )
                | self.relevance_analyzer_prompt.with_config(
                    {"run_name": "ChatPromptTemplate_RelevanceAnalyzer"}
                )
                | RunnableLambda(self._log_full_prompt).with_config(
                    {"run_name": "FULL_PROMPT_RelevanceAnalyzer"}
                )
                | self.llm.with_config({"run_name": "Gemini_RelevanceAnalyzer"})
                | StrOutputParser().with_config(
                    {"run_name": "RelevanceAnalyzer_Output"}
                )
            )
        else:
            self.structured_formatter_chain = None
            self.context_summarizer_chain = None
            self.relevance_analyzer_chain = None

        # Build the graph after all components are initialized
        self.graph = self._build_graph()

    # --- Logging Helper Methods ---

    def _log_prompt_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to log prompt input for better LangSmith visibility."""
        return {
            **input_data,
            "_langsmith_metadata": {"input_type": "ChatPromptTemplate_Variables"},
        }

    def _log_full_prompt(self, messages) -> Any:
        """Helper method to log the complete formatted prompt."""
        return messages

    # --- Graph Definition ---

    def _build_graph(self):
        """Build the LangGraph state graph with routing."""
        workflow = StateGraph(SearchState)

        workflow.add_node("validate_input", self._validate_input)
        workflow.add_node("search_documents", self._search_documents)
        workflow.add_node("prepare_context", self._prepare_context)
        workflow.add_node("summarize_results", self._summarize_results)
        workflow.add_node("analyze_results", self._analyze_results)
        workflow.add_node("format_structured", self._format_results_structured)
        workflow.add_node("handle_error", self._handle_error)

        workflow.set_entry_point("validate_input")

        workflow.add_conditional_edges(
            "validate_input",
            self._should_continue_after_validation,
            {"continue": "search_documents", "error": "handle_error"},
        )
        workflow.add_conditional_edges(
            "search_documents",
            self._should_continue_after_search,
            {"continue": "prepare_context", "error": "handle_error"},
        )

        workflow.add_conditional_edges(
            "prepare_context",
            self._route_to_processor,
            {
                "summary": "summarize_results",
                "analysis": "analyze_results",
                "structured": "format_structured",
            },
        )

        workflow.add_edge("summarize_results", END)
        workflow.add_edge("analyze_results", END)
        workflow.add_edge("format_structured", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile()

    # --- Graph Node Methods ---

    @traceable(name="validate_input")
    async def _validate_input(self, state: SearchState) -> SearchState:
        """Validate input parameters."""
        if not state["query"].strip():
            state["error"] = "Query cannot be empty"
        elif state["top_k"] <= 0:
            state["error"] = "top_k must be greater than 0"
        return state

    @traceable(name="search_documents")
    async def _search_documents(self, state: SearchState) -> SearchState:
        """Perform document search."""
        import time

        start_time = time.time()

        try:
            # Add timeout wrapper at node level too (45 seconds)
            documents = await asyncio.wait_for(
                self.search_client.search_documents(
                    query=state["query"], top_k=state["top_k"]
                ),
                timeout=45.0,
            )

            state["documents"] = self.search_client.documents_to_dict(documents)

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            error_msg = f"Node search timed out after {elapsed:.2f} seconds"
            logger.error(error_msg)
            state["error"] = error_msg
            state["documents"] = []

        except Exception as e:
            elapsed = time.time() - start_time
            import traceback
            traceback.print_exc(file=sys.stderr)
            logger.error(f"Search failed: {e}")
            state["error"] = f"Search error: {e}"
            state["documents"] = []

        return state

    @traceable(name="prepare_context")
    async def _prepare_context(self, state: SearchState) -> SearchState:
        """Prepares the raw context from documents for LLM processing."""
        if not state["documents"]:
            state["raw_context"] = "No documents found for the given query."
            return state

        context_parts = []
        for i, doc in enumerate(state["documents"], 1):
            content = doc.get("content", "")
            title = doc.get("title", f"Document {i}")
            doc_section = f"## {title}\n\n{content}"
            context_parts.append(doc_section)

        state["raw_context"] = "\n\n---\n\n".join(context_parts)
        return state

    @traceable(name="summarize_results")
    async def _summarize_results(self, state: SearchState) -> SearchState:
        """Node that invokes the summarization LCEL chain."""
        if not self.context_summarizer_chain:
            state["error"] = "Summarizer chain is not available (LLM not configured)."
            return state

        try:
            summary = await self.context_summarizer_chain.ainvoke(
                {"query": state["query"], "documents": state["raw_context"]}
            )
            state["context"] = summary

        except Exception as e:
            print(f"!!! NODE ERROR IN SUMMARIZATION: {e} !!!", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            state["error"] = f"Error during summarization: {e}"

        return state

    @traceable(name="analyze_results")
    async def _analyze_results(self, state: SearchState) -> SearchState:
        """Node that invokes the relevance analysis LCEL chain."""
        if not self.relevance_analyzer_chain:
            state["error"] = "Analyzer chain is not available (LLM not configured)."
            return state

        try:
            analysis = await self.relevance_analyzer_chain.ainvoke(
                {"query": state["query"], "documents": state["raw_context"]}
            )
            state["context"] = analysis

        except Exception as e:
            print(f"!!! NODE ERROR IN ANALYSIS: {e} !!!", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            state["error"] = f"Error during analysis: {e}"

        return state

    @traceable(name="format_results_structured")
    async def _format_results_structured(self, state: SearchState) -> SearchState:
        """Node that invokes the document formatting LCEL chain."""
        if not self.structured_formatter_chain:
            state["context"] = (
                f"Found {len(state['documents'])} documents.\n\n{state['raw_context']}"
            )
            return state
        try:
            formatted_docs = await self.structured_formatter_chain.ainvoke(
                {
                    "query": state["query"],
                    "documents": state["raw_context"],
                    "num_results": len(state["documents"]),
                }
            )
            state["context"] = formatted_docs
        except Exception as e:
            state["error"] = f"Error during structured formatting: {e}"
        return state

    async def _handle_error(self, state: SearchState) -> SearchState:
        """Handle errors in the chain."""
        error_msg = state.get("error", "Unknown error occurred")
        logger.error(f"Handling error: {error_msg}")
        state["context"] = f"Error: {error_msg}"
        return state

    # --- Graph Conditional Edges / Routers ---

    def _should_continue_after_validation(self, state: SearchState) -> str:
        return "error" if state.get("error") else "continue"

    def _should_continue_after_search(self, state: SearchState) -> str:
        return "error" if state.get("error") else "continue"

    def _route_to_processor(self, state: SearchState) -> str:
        """Router to decide which processing node to use."""
        return state["output_format"]

    # --- Main Public Methods ---

    @traceable(name="azure_search_chain")
    async def run(
        self,
        query: str,
        search_type: str = "text",
        top_k: int = 5,
        output_format: str = "analysis",  # Defaults to analysis
    ) -> Dict[str, Any]:
        """Run the search chain with a specified output format."""
        initial_state = SearchState(
            query=query,
            search_type=search_type,
            top_k=top_k,
            output_format=output_format,
            documents=[],
            context="",
            raw_context="",
            metadata={},
            error=None,
        )

        try:
            # Add timeout to graph execution to prevent hanging
            result = await asyncio.wait_for(
                self.graph.ainvoke(initial_state), timeout=25.0
            )

        except asyncio.TimeoutError:
            print(
                "!!! CRITICAL TIMEOUT IN CHAIN GRAPH EXECUTION after 25s !!!", 
                file=sys.stderr
            )
            raise Exception("Chain graph execution timed out after 25 seconds")

        except Exception as e:
            print(
                f"!!! CRITICAL ERROR IN CHAIN GRAPH EXECUTION: {e} !!!", file=sys.stderr
            )
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise

        result["metadata"] = {
            "total_results": len(result.get("documents", [])),
            "search_type": result.get("search_type"),
            "query": result.get("query"),
            "output_format": result.get("output_format"),
            "used_llm": bool(self.llm),
        }

        final_result = {
            "context": result["context"],
            "metadata": result["metadata"],
            "documents": result["documents"],
            "success": not bool(result.get("error")),
        }

        return final_result

    async def get_document_context_tool(self, document_ids: str) -> str:
        """Tool function to get context from specific documents by ID."""
        try:
            ids = [id.strip() for id in document_ids.split(",") if id.strip()]
            if not ids:
                return "Error: No valid document IDs provided"

            documents = await self.search_client.get_document_context(ids)
            if not documents:
                return "No documents found for the provided IDs"

            context_parts = []
            for doc in documents:
                if hasattr(doc, "page_content") and hasattr(doc, "metadata"):
                    title = doc.metadata.get("title", "Untitled")
                    content = doc.page_content or "No content available"
                    context_parts.append(f"**{title}**\n{content}")

            return "\n\n---\n\n".join(context_parts)
        except Exception as e:
            return f"Error retrieving document context: {e}"

    def print_graph_diagram(self):
        """Print a simple representation of the graph structure."""
        try:
            graph_repr = self.graph.get_graph()
            nodes = list(graph_repr.nodes.keys())
            print("LangGraph Chain Structure:")
            print(f"Nodes: {', '.join([n for n in nodes if not n.startswith('__')])}")
        except Exception:
            print("Graph structure visualization not available")

    async def close(self):
        """Clean up resources."""
        await self.search_client.close()
