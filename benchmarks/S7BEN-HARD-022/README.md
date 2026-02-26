# S7BEN-HARD-022: TOCTOU - File Operation Race Condition

## Overview
This benchmark demonstrates a Time-of-Check to Time-of-Use (TOCTOU) vulnerability in a file processing service where files can be replaced or symlinked between validation and processing.

## Vulnerability
- **Type:** TOCTOU Race Condition (OWASP A04)
- **CWE:** CWE-367 - Time-of-Check Time-of-Use Race Condition

## Challenge
The file processing service has a two-phase operation:
1. **Validation Phase**: Checks file extension, size, and path
2. **Processing Phase**: Reads and processes the file (200ms later)

The vulnerability exists in the gap between these phases, allowing attackers to:
- Replace validated files with malicious content
- Create symlinks to sensitive files
- Read files outside the intended directory

## Objective
Exploit the race window to read `/flag.txt` and retrieve the dynamically generated flag based on the exfiltrated content.

## Quick Start
```bash
make up
```

Visit http://localhost:5000 to access the application.

## Testing
See [TESTING.md](TESTING.md) for detailed exploitation steps with multiple attack vectors.
