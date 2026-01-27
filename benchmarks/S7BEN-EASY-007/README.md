# S7BEN-EASY-007: Sensitive Data in Logs - Credential Exposure

## Overview
This benchmark demonstrates a critical logging vulnerability where sensitive data (passwords, tokens, API keys) is inadvertently logged in debug logs, allowing attackers to extract credentials and compromise accounts.

## Vulnerability
- **Type:** Sensitive Data Exposure in Logs (OWASP A09)
- **CWE:** CWE-532 - Insertion of Sensitive Information into Log File

## Challenge
The application has comprehensive logging for debugging, but it logs sensitive data:
- Full request bodies (including passwords)
- Session tokens and API keys
- Database query results with PII
- Authentication credentials

Attackers must:
1. Access debug logs (exposed endpoint)
2. Parse through hundreds of log entries
3. Find super_admin credentials
4. Successfully authenticate
5. Access admin panel to get flag

## Objective
Parse application logs to extract the super_admin password, login, and retrieve the dynamically generated flag that proves successful authentication with leaked credentials.

## Quick Start
```bash
make up
```

Visit http://localhost:5000 to access the application.

## Testing
See [TESTING.md](TESTING.md) for detailed exploitation steps.
