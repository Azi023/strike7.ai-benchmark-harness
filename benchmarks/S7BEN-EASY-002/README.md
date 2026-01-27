# S7BEN-EASY-002: Hardcoded Secrets - API Key Exposure

## Overview
This benchmark demonstrates a critical cryptographic failure where API keys are hardcoded in client-side JavaScript, making them accessible to anyone who views the source.

## Vulnerability
- **Type:** Hardcoded Secrets (OWASP A02)
- **CWE:** CWE-798 - Use of Hard-coded Credentials

## Challenge
The application includes an API key directly in the JavaScript source code. Attackers can:
1. View the page source or JavaScript files
2. Extract the hardcoded API key
3. Use the key to access protected endpoints

## Objective
Find the API key in the JavaScript source and use it to access the `/api/secret` endpoint to retrieve the flag.

## Quick Start
```bash
make up
```

Visit http://localhost:5000 to access the application.

## Testing
See [TESTING.md](TESTING.md) for detailed exploitation steps.
