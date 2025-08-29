# Claude Desktop MCP Integration Setup Guide

## Overview
This guide will help you integrate your Azure AI Search MCP server with Claude Desktop, allowing Claude to directly query your Azure AI Search index for document retrieval and analysis.

## Prerequisites
✅ MCP Server working (you've already tested this)  
✅ Azure AI Search configured with documents  
✅ Claude Desktop installed on your machine  

## Step 1: Locate Claude Desktop Configuration

Claude Desktop stores its configuration in a JSON file at:

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Example full path:**
```
C:\Users\{USERNAME}\AppData\Roaming\Claude\claude_desktop_config.json
```

## Step 2: MCP Server Configuration

Add this configuration to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "azure-search-mcp": {
      "command": "../AppData/Local/anaconda3/Scripts/conda.exe",
      "args": [
        "run", 
        "-p", 
        "..\\AppData\\Local\\anaconda3", 
        "--no-capture-output",
        "python", 
        "-m", 
        "azure_search_mcp"
      ],
      "cwd": "..\\langgraph-claude-azure-mcp",
      "env": {
        "PYTHONPATH": "..\\langgraph-claude-azure-mcp\\src"
      }
    }
  }
}
```

## Step 3: Environment Variables

Ensure your `.env` file is in the project root directory:
```
<project-directory>\.env
```

And contains:
```
# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_API_KEY=your_api_key_here
AZURE_SEARCH_INDEX_NAME=your-index-name

# LangSmith Configuration (Optional - for tracing and monitoring)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=azure-search-mcp
```

### 3.1 LangSmith Setup (Optional but Recommended)

LangSmith provides excellent tracing and monitoring for your MCP server:

1. **Sign up for LangSmith**: Visit [smith.langchain.com](https://smith.langchain.com)
2. **Get your API key**: Go to Settings → API Keys → Create API Key
3. **Update your `.env` file** with your real LangSmith API key:
   ```
   LANGCHAIN_API_KEY=lsv2_pt_your_actual_api_key_here
   ```
4. **Test the integration**:
   ```bash
   python test_langsmith.py
   ```

**Benefits of LangSmith integration:**
- 📊 Trace all search operations and performance metrics
- 🔍 Debug issues with search queries and results  
- 📈 Monitor usage patterns and response times
- 🚨 Get alerts for errors or performance issues
- 🔗 View detailed execution traces for each Claude interaction

**What gets traced:**
- ✅ Individual tool calls from Claude
- ✅ Azure AI Search query execution  
- ✅ Document retrieval and formatting
- ✅ LangGraph workflow execution
- ✅ Performance metrics and timing

## Step 4: Integration Steps

### 4.1 Find Claude Desktop Config
1. Open File Explorer
2. Press `Win + R`, type `%APPDATA%` and press Enter
3. Navigate to `Claude` folder
4. Look for `claude_desktop_config.json`

### 4.2 Update Configuration
If the file exists:
- Open it and add the `mcpServers` section above

If the file doesn't exist:
- Create it with the complete JSON configuration above

### 4.3 Restart Claude Desktop
1. Completely close Claude Desktop
2. Restart the application
3. Claude should now have access to your MCP tools

## Step 5: Available Tools in Claude

Once integrated, Claude will have access to these tools:

### 🔍 search_documents
Search for relevant documents with structured formatting
- **query**: Your search terms
- **top_k**: Number of results (default: 5)  
- **format_type**: "structured", "summary", or "analysis"

### 📋 search_and_summarize
Search and get a summarized view of results
- **query**: Your search terms
- **top_k**: Number of results (default: 5)

### 🔬 search_with_analysis
Search with relevance analysis
- **query**: Your search terms
- **top_k**: Number of results (default: 5)

### 📄 get_document_context
Get detailed context from specific documents
- **document_ids**: Comma-separated document IDs
- **format_output**: Whether to format output (default: true)

## Step 6: Testing the Integration

Ask Claude to:

1. **Search for CEO compensation:**
   ```
   "Can you search for CEO compensation information using the Azure Search tool?"
   ```

2. **Analyze executive pay:**
   ```
   "Use the search tool to find and analyze executive compensation data"
   ```

3. **Get document summaries:**
   ```
   "Search for salary information and provide a summary"
   ```

## Troubleshooting

### Issue: Claude doesn't see the tools
- **Solution**: Check the config file path and restart Claude Desktop completely

### Issue: MCP server fails to start
- **Solution**: Test the server manually:
  ```bash
  cd <project-directory>\src
  python -m azure_search_mcp
  ```

### Issue: Authentication errors
- **Solution**: Verify your `.env` file has the correct Azure Search credentials

### Issue: No search results
- **Solution**: Test your Azure Search index manually to ensure it has documents

## Step 7: Example Claude Interactions

Once set up, you can ask Claude:

```
"Search for information about CEO compensation and executive pay packages"
```

Claude will use your MCP server to query Azure AI Search and return formatted results with CEO compensation data from your documents.

## Step 8: LangSmith Monitoring (Optional)

If you configured LangSmith, you can monitor your MCP server:

1. **View traces**: Visit [smith.langchain.com](https://smith.langchain.com)
2. **Check your project**: Look for the `azure-search-mcp` project
3. **Monitor performance**: See execution times, success rates, and errors
4. **Debug issues**: Trace individual search queries and their results

**What you'll see in LangSmith:**
- 🔍 Each search query Claude makes
- ⏱️ Response times for Azure AI Search
- 📊 Document retrieval statistics  
- 🚨 Any errors or performance issues
- 📈 Usage patterns over time

## Configuration Files Summary

**Claude Desktop Config Location:**
```
C:\Users\manasa.mallipeddi\AppData\Roaming\Claude\claude_desktop_config.json
```

**Your MCP Server Location:**  
```
c:\Users\manasa.mallipeddi\Documents\RAG\MCP-POC\src\azure_search_mcp\
```

**Environment Variables:**
```
c:\Users\manasa.mallipeddi\Documents\RAG\MCP-POC\.env
```

**LangSmith Integration:**
- ✅ Tracing configured and ready
- 📊 Monitors all search operations  
- 🔗 Dashboard: https://smith.langchain.com
- 🧪 Test with: `python test_langsmith.py`

---

🎉 **You're all set!** Your Azure AI Search MCP server is ready to be integrated with Claude Desktop for intelligent document retrieval and analysis, with optional LangSmith monitoring for performance insights.
