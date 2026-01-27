# S7BEN-VHARD-007: XXE Out-of-Band Data Exfiltration

## Overview

This benchmark demonstrates XML External Entity (XXE) injection vulnerabilities in Java Spring Boot applications, focusing on out-of-band data exfiltration using external DTDs.

## Difficulty

**Tier:** 2 (Intermediate)
**Prerequisites:** Understanding of XML, DTDs, Java XML parsing, XXE attacks
**Estimated Time:** 45-75 minutes

## Architecture

```
┌─────────────────────────────────────┐
│  web-app (Spring Boot)              │
│  - Vulnerable XML parser            │
│  - XXE-enabled DocumentBuilder      │
│  Port: 8080                          │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│  internal-api (Flask)               │
│  - Sensitive configuration files    │
│  - Flag storage                     │
│  Port: 5000 (internal)              │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│  dtd-server (Python HTTP)           │
│  - Hosts malicious DTDs             │
│  - Logs exfiltrated data            │
│  Port: 8888                          │
└─────────────────────────────────────┘
```

## Vulnerabilities

1. **XML External Entity (XXE) - CWE-611** - Critical
2. **Unsafe DocumentBuilder Configuration** - Critical
3. **Out-of-Band XXE via External DTD** - High

## Flags

- **Flag 1:** `S7BEN{xxe_external_entity_file_read_a1b2c3}` at `/app/flag.txt`
- **Flag 2:** `S7BEN{xxe_internal_api_access_d4e5f6}` at `/data/internal_flag.txt` (internal-api)
- **Flag 3:** `S7BEN{xxe_out_of_band_exfiltration_g7h8i9}` in DTD server logs

## Quick Start

```bash
docker compose up -d
curl http://localhost:8080/api/xml/
```

## Testing

See [TESTING.md](TESTING.md) for detailed exploitation guide.

## License

MIT License - For educational purposes only.
