# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it privately to help us address it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by:

1. **Email**: Send an email to [manasam@lensfashion.com] with:
   - A clear description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Any suggested fixes (if available)

2. **GitHub Security Advisories**: Use GitHub's [private security advisory reporting](https://github.com/codewith-mm/langgraph-claude-azure-mcp/security/advisories/new)

### What to Expect

- **Acknowledgment**: We'll acknowledge receipt of your report within 48 hours
- **Assessment**: We'll assess the vulnerability and determine its severity within 5 business days
- **Updates**: We'll provide regular updates on our progress
- **Resolution**: We'll work to address confirmed vulnerabilities promptly
- **Credit**: With your permission, we'll credit you for the discovery

## Security Considerations

### API Keys and Credentials

This project requires sensitive credentials including:
- Azure AI Search API keys
- Google Gemini API keys (optional)
- LangSmith API keys (optional)

**Important Security Practices:**

1. **Never commit credentials**: Always use `.env` files and ensure they're in `.gitignore`
2. **Environment isolation**: Use different credentials for development, staging, and production
3. **Key rotation**: Regularly rotate API keys and credentials
4. **Minimal permissions**: Use least-privilege access for all service accounts
5. **Monitoring**: Monitor API usage for suspicious activity

### Azure AI Search Security

- Use Azure Managed Identity when possible instead of API keys
- Configure IP restrictions on your Azure AI Search service
- Enable audit logging for search operations
- Use HTTPS for all communications

### Network Security

- This MCP server runs locally and communicates with:
  - Azure AI Search service (outbound HTTPS)
  - Google Gemini API (outbound HTTPS, optional)
  - LangSmith API (outbound HTTPS, optional)
  - Claude Desktop (local IPC)

### Data Privacy

- Search queries and results may contain sensitive information
- Consider data residency requirements for your use case
- Review Azure AI Search data processing agreements
- Implement appropriate data retention policies

## Known Security Limitations

1. **Local execution**: This MCP server runs with the permissions of the user account
2. **Credential storage**: API keys are stored in local environment variables
3. **Network communications**: Relies on HTTPS for external API security

## Security Updates

Security updates will be published as new releases with detailed security advisories. Monitor this repository for security-related announcements.

## Contact

For security-related questions or concerns, contact: @codewith-mm
