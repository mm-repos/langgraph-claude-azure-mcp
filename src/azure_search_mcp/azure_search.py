"""Azure AI Search retriever implementation using LangChain."""

import asyncio
import sys
import time
from typing import Any, Dict, List, Optional

from langchain.schema import Document
from langchain_community.retrievers import AzureAISearchRetriever

from .config import config


class AzureSearchClient:
    """Azure AI Search client using LangChain's AzureAISearchRetriever."""

    def __init__(self):
        """Initialize the Azure Search retriever."""
        self.endpoint = config.azure_search.endpoint
        self.api_key = config.azure_search.api_key
        self.index_name = config.azure_search.index_name
        self.retriever = None
        self._init_error = None

        if not all([self.endpoint, self.api_key, self.index_name]):
            missing_vars = []
            if not self.endpoint:
                missing_vars.append("AZURE_SEARCH_ENDPOINT")
            if not self.api_key:
                missing_vars.append("AZURE_SEARCH_API_KEY")
            if not self.index_name:
                missing_vars.append("AZURE_SEARCH_INDEX_NAME")

            self._init_error = f"Azure Search configuration is incomplete. Missing environment variables: {', '.join(missing_vars)}"
            print(f"[AZURE_SEARCH_CONFIG_ERROR] {self._init_error}", file=sys.stderr)
            return

        try:
            # Initialize the LangChain AzureAISearchRetriever
            self.retriever = AzureAISearchRetriever(
                service_name=self._extract_service_name(self.endpoint),
                index_name=self.index_name,
                api_key=self.api_key,
                content_key="content",  # Field name for document content
                top_k=5,  # Default number of results
            )
        except Exception as e:
            self._init_error = f"Failed to initialize Azure Search retriever: {str(e)}"
            print(f"[AZURE_SEARCH_INIT_ERROR] {self._init_error}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)

    def _extract_service_name(self, endpoint: str) -> str:
        """Extract service name from Azure Search endpoint."""
        # Extract service name from https://servicename.search.windows.net
        if endpoint.startswith("https://"):
            service_name = endpoint.split("//")[1].split(".")[0]
            return service_name
        else:
            raise ValueError(f"Invalid Azure Search endpoint format: {endpoint}")

    async def search_documents(self, query: str, top_k: int = 5) -> List[Document]:
        """Search for documents using text query."""
        start_time = time.time()

        # Check if initialization failed
        if self._init_error:
            raise Exception(f"Azure Search not properly configured: {self._init_error}")

        if not self.retriever:
            error_msg = "Azure Search retriever not initialized"
            raise Exception(error_msg)

        try:
            # Update retriever with new top_k if different
            if self.retriever.top_k != top_k:
                self.retriever.top_k = top_k

            # Add timeout wrapper to prevent hanging
            async def _execute_search():
                # Force sync method to avoid hanging async issues
                try:
                    # Always use sync method in executor to avoid async deadlocks
                    loop = asyncio.get_event_loop()

                    # Ensure retriever exists (already checked above but for type safety)
                    if not self.retriever:
                        raise Exception("Retriever not available")

                    # Add inner timeout for the sync call
                    documents = await asyncio.wait_for(
                        loop.run_in_executor(None, self.retriever.invoke, query),
                        timeout=25.0,  # 5 seconds less than outer timeout
                    )

                    return documents

                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    raise

                except Exception as sync_error:
                    elapsed = time.time() - start_time
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                    raise sync_error

            # Execute with timeout (30 seconds)
            documents = await asyncio.wait_for(_execute_search(), timeout=30.0)
            return documents

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            raise Exception(f"Azure Search timed out after {elapsed:.2f} seconds")

        except Exception as e:
            elapsed = time.time() - start_time
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise Exception(f"Error searching documents: {str(e)}")

    async def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """Retrieve a specific document by ID (if supported by index)."""
        try:
            # For now, we'll search by ID as a query
            # This is a workaround since AzureAISearchRetriever doesn't have direct ID lookup
            documents = await self.search_documents(f"id:{document_id}", top_k=1)
            return documents[0] if documents else None
        except Exception as e:
            raise Exception(f"Error retrieving document {document_id}: {str(e)}")

    async def get_document_context(self, document_ids: List[str]) -> List[Document]:
        """Retrieve multiple documents by their IDs."""
        documents = []
        for doc_id in document_ids:
            try:
                doc = await self.get_document_by_id(doc_id)
                if doc:
                    documents.append(doc)
            except Exception as e:
                # Log error but continue with other documents
                print(
                    f"Warning: Could not retrieve document {doc_id}: {str(e)}",
                    file=sys.stderr,
                )
                continue

        return documents

    def documents_to_dict(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Convert LangChain Document objects to dictionaries."""
        result = []
        for doc in documents:
            doc_dict = {"content": doc.page_content, **doc.metadata}
            result.append(doc_dict)
        return result

    async def close(self):
        """Close the search client (cleanup if needed)."""
        # AzureAISearchRetriever doesn't require explicit cleanup
        pass
