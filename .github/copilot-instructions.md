# Azure AI Search MCP Server

## Project Overview

This project is a **Model Context Protocol (MCP) server** that provides seamless integration with **Azure AI Search** services. The server enables AI assistants and applications to perform intelligent search operations across indexed documents and data sources.

### Key Technologies
- **Python 3.8+** - Core development language
- **LangChain/LangGraph** - AI workflow orchestration and chaining
- **Azure AI Search** - Cloud-based search service integration
- **Google Gemini** - Large language model for enhanced document processing
- **MCP Protocol** - Standard protocol for AI model context sharing
- **LangSmith** - Observability and tracing for AI chain executions
- **Pydantic** - Type-safe configuration validation and data models
- **python-dotenv** - Environment variable management and secure secrets handling

### Core Functionality
- **Document Search**: Intelligent search across Azure AI Search indexes
- **Chain Processing**: LangGraph-based workflow execution for complex queries
- **AI-Enhanced Processing**: Google Gemini integration for document formatting, summarization, and analysis
- **MCP Compliance**: Full Model Context Protocol implementation
- **Prompt Management**: Dynamic prompt templating and management system
- **Real-time Integration**: Live connection to Azure AI Search services
- **Observability**: Comprehensive tracing and monitoring with LangSmith

### Architecture Components
- `azure_search.py` - Azure AI Search client and operations
- `chain.py` - LangGraph chain definitions and workflow logic
- `server.py` - MCP server implementation and protocol handlers
- `prompt_manager.py` - Dynamic prompt template management
- `config.py` - Configuration management and environment setup

### Development Status
- ✅ Core MCP server functionality
- ✅ Azure AI Search integration
- ✅ Google Gemini integration with proper LangChain chains
- ✅ LangGraph chain processing
- ✅ LangSmith tracing and observability
- ✅ Prompt management system
- ✅ Comprehensive testing suite
- ✅ Pydantic-based configuration validation

---

## Code Style and Conventions

### Python Standards
- **Follow PEP 8** for code formatting and style
- **Use type hints** for all function parameters and return values
- **Write comprehensive docstrings** using Google or NumPy style
- **Maximum line length**: 88 characters (Black formatter standard)
- **Use f-strings** for string formatting over `.format()` or `%` formatting

### Naming Conventions
- **Classes**: PascalCase (e.g., `AzureSearchClient`, `PromptManager`)
- **Functions/Variables**: snake_case (e.g., `search_documents`, `prompt_template`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_INDEX_NAME`, `MAX_RESULTS`)
- **Private methods**: Leading underscore (e.g., `_validate_config`)
- **MCP tools**: Descriptive names with context (e.g., `search_azure_documents`)

### File Organization
- **One class per file** when possible
- **Group related functions** in modules logically
- **Import order**: standard library → third-party → local imports
- **Use `__all__`** to explicitly define public API in modules

### Documentation Standards
- **Module docstrings**: Purpose, usage examples, key classes/functions
- **Function docstrings**: Args, Returns, Raises with types
- **Class docstrings**: Purpose, key methods, usage patterns
- **Inline comments**: Explain complex logic, not obvious code

---

## Development Workflow

### Environment Setup
- **Python 3.8+** required for development
- **Use conda/venv** for isolated environments
- **Install in development mode**: `pip install -e .`
- **Pre-commit hooks**: Install for code quality checks
- **Environment variables**: Use `.env` file for local development

### Testing Procedures
- **Run tests before commits**: `pytest tests/`
- **Maintain test coverage**: Aim for >80% coverage
- **Test categories**:
  - Unit tests: Individual component testing
  - Integration tests: Azure AI Search connectivity
  - Chain tests: LangGraph workflow validation
- **Use fixtures**: For common test setups and mock data

### Commit Standards
- **Conventional Commits**: Use standard prefixes
  - `feat:` - New features
  - `fix:` - Bug fixes
  - `docs:` - Documentation changes
  - `test:` - Test additions/modifications
  - `refactor:` - Code restructuring
- **Clear descriptions**: Explain what and why, not just what
- **Small, focused commits**: One logical change per commit

### Code Review Guidelines
- **Review checklist**: Functionality, performance, security, style
- **Test coverage**: Ensure new code includes appropriate tests
- **Documentation**: Update docs for public API changes
- **Breaking changes**: Clearly document and discuss impact

---

## Copilot Behavior Guidelines

### Core Principles
- **Your Persona**: You are an expert Python developer with deep expertise in Azure, AI services, and building robust backend systems. Your primary goal is to assist in writing clean, testable, and maintainable code that strictly adheres to this project's standards.
- **Proactive but Cautious**: Always think ahead and suggest best practices, but **never** take action without approval. This includes creating files, modifying code, or adding dependencies.
- **Explain First, Then Act**: For any non-trivial suggestion, first explain *what* you propose to do and *why* it's the right approach, referencing the guidelines in this document.

### Things to AVOID
- **NEVER** hardcode secrets, API keys, or any sensitive credentials. Always refer to environment variables as defined in our configuration standards.
- **NEVER** suggest deprecated libraries or functions without asking or confirming.
- **NEVER** write implementation code without also providing the corresponding unit or integration tests.
- **NEVER** commit directly. Your role is to only help write and stage code.

### Interaction Protocols

- **File Creation Protocol**: Before creating any new files, you must:
  1.  **Present at least 2 options** for the file structure/approach.
  2.  **Explain your recommended choice** and why it aligns with our architecture.
  3.  **Wait for user approval** before proceeding.
  4.  **Show a preview** of the file contents before writing them.

- **Modification Protocol**: For changes to existing files:
  1.  **Summarize the requested changes** and their impact on other components.
  2.  **Highlight any affected dependencies** or potential breaking changes.
  3.  **Suggest a testing strategy** for validating the changes.

- **Dependency Protocol**: Before adding a new dependency:
  1.  State the purpose of the new package.
  2.  Confirm it is actively maintained and secure.
  3.  Provide the exact command to add it (e.g., `pip install some-package`).
  4.  Wait for user approval.

- **Debugging Protocol**: When provided with an error or traceback:
  1.  Analyze the error in the context of our codebase (`server.py`, `chain.py`, etc.).
  2.  Propose the most likely cause.
  3.  Suggest a specific code fix, including necessary changes to tests.

- **Documentation Protocol**:
  - Any debugging documentation, troubleshooting guides, or development notes should be placed in the `docs/development/` directory.
  - All public functions and classes must have complete Google-style docstrings before the task is considered done.

- **Testing Protocol**:
  - All test files must be placed in the `tests/` directory.
  - All new features (`feat:`) or bug fixes (`fix:`) must be accompanied by corresponding tests. You must help create or update these tests.

---

## Architecture Guidelines

### MCP Server Best Practices
- **Tool definitions**: Clear, descriptive names and parameters
- **Error handling**: Graceful failures with informative messages
- **Resource management**: Proper cleanup of connections and resources
- **Logging**: Structured logging for debugging and monitoring
- **Configuration**: Environment-based config with sensible defaults

### Azure AI Search Integration
- **Connection pooling**: Reuse search clients when possible
- **Query optimization**: Use appropriate search parameters and filters
- **Result handling**: Implement pagination and result limiting
- **Error recovery**: Handle service unavailability and rate limiting
- **Security**: Use managed identity or secure credential storage

### LangGraph Chain Development
- **Node design**: Single responsibility, clear input/output contracts
- **State management**: Minimize state, use typed state objects
- **Error propagation**: Handle chain failures gracefully
- **Observability**: Include tracing and metrics for chain execution
- **Testing**: Mock external dependencies for reliable testing

### Google Gemini Integration
- **Chain composition**: Use proper LangChain syntax (prompt | llm | parser)
- **Model configuration**: Configure temperature, model selection appropriately
- **Graceful fallbacks**: Handle API failures with basic formatting fallbacks
- **Traceability**: Ensure all LLM calls are properly traced in LangSmith
- **Cost optimization**: Use appropriate models and parameters for each use case

### Prompt Management
- **Template versioning**: Track prompt template changes over time
- **Dynamic loading**: Support runtime prompt updates without restart
- **Validation**: Ensure prompt templates are valid and complete
- **Fallbacks**: Default prompts when custom templates fail
- **Testing**: Validate prompt outputs with expected responses

---

## Security and Configuration Guidelines

### Environment Variables and Secrets
- **Never commit secrets**: Use `.env` files for local development (add to `.gitignore`)
- **python-dotenv**: Use python-dotenv for secure environment variable loading
- **Azure credentials**: Use Azure Managed Identity or Azure Key Vault when possible
- **Environment-specific configs**: Separate configs for dev, staging, production
- **Required variables**: Document all required environment variables in README
- **Validation**: Validate required environment variables at startup

### Azure AI Search Security
- **API key rotation**: Implement regular API key rotation procedures
- **Network security**: Use private endpoints when available
- **Access control**: Implement least-privilege access principles
- **Query sanitization**: Sanitize and validate all search queries
- **Rate limiting**: Implement client-side rate limiting for API calls

### Configuration Management
- **Config validation**: Use Pydantic models for configuration validation
- **Type safety**: Leverage Pydantic's type validation for robust configuration
- **Default values**: Provide sensible defaults for non-sensitive settings
- **Environment detection**: Auto-detect development vs production environments
- **Config hierarchy**: Support multiple config sources (env vars > config files > defaults)
- **Hot reload**: Support configuration changes without service restart where appropriate

### Data Security and Privacy
- **Input sanitization**: Validate and sanitize all user inputs
- **Output filtering**: Filter sensitive information from responses
- **Audit logging**: Log all search operations for security auditing
- **Data retention**: Implement appropriate data retention policies
- **Encryption**: Use HTTPS for all external communications

### Error Handling and Information Disclosure
- **Safe error messages**: Don't expose internal system details in error messages
- **Structured logging**: Use structured logging with appropriate log levels
- **Health checks**: Implement health endpoints that don't expose sensitive info
- **Monitoring**: Set up proper monitoring and alerting for security events

---

## Project Completeness and Documentation

### Guiding Principles
- **Running and Debugging**: When asked how to run or debug the project, refer to the `Development Workflow` section of these instructions and provide clear, step-by-step commands. If a VS Code `tasks.json` or `launch.json` is needed, propose a configuration based on the project structure and `server.py` implementation, and wait for approval before creating it.
- **Documentation as a Source of Truth**: At the end of a major feature implementation or refactoring effort, you should assist in reviewing the main `README.md`. Your goal is to help ensure it accurately reflects the current project status, setup instructions, and required environment variables.
- **Instruction Integrity**: You should be aware of these instructions (`.github/copilot-instructions.md`) and help update them if we decide to change a workflow or standard.