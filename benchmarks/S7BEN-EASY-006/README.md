# S7BEN-EASY-006: Log Injection - Forge Log Entries

## Overview
This benchmark demonstrates log injection vulnerability where unsanitized user input is written to logs, allowing attackers to forge fake log entries and bypass security monitoring.

## Vulnerability
- **Type:** Log Injection (OWASP A09)
- **CWE:** CWE-117 - Improper Output Neutralization for Logs

## Challenge
The application logs login attempts with unsanitized username input. Attackers can:
1. Inject newline characters to create fake log entries
2. Hide malicious activity by injecting false success messages
3. Bypass SIEM and log analysis tools
4. Create false audit trails

## Objective
Inject a forged log entry showing a successful admin login from a trusted IP (127.0.0.1), then verify your injection to retrieve the flag.

## Quick Start
```bash
make up
```

Visit http://localhost:5000 to access the application.

## Testing
See [TESTING.md](TESTING.md) for detailed exploitation steps.
