# S7BEN-EASY-008: Error-Based Information Disclosure - Training

## Overview

This benchmark demonstrates **Error-Based Information Disclosure** - a critical vulnerability newly highlighted in **OWASP Top 10 2025 (A10)**.

**Tier:** Training (T1) - Hints provided  
**Difficulty:** Easy  
**OWASP 2025:** A10 - Mishandling of Exceptional Conditions  
**CWE:** CWE-209, CWE-497

---

## Quick Start

```bash
cd benchmarks/S7BEN-EASY-008
make build
make up
```

Access: http://localhost:5000

---

## Vulnerability

The application exposes sensitive information through error messages:
- Database credentials
- Internal file paths
- Configuration details
- Stack traces

---

## Exploitation Path

1. Trigger error with `/user/abc`
2. Find `db_password` in error response
3. Use password at `/admin/login`
4. Retrieve flag

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/user/<id>` | User lookup (type error) |
| `/file/<name>` | File reader (path disclosure) |
| `/search` | Search (DB error) |
| `/admin/login` | Use extracted creds |
| `/api/oracle` | Expected state |
| `/api/verify` | Verify exploitation |

---

## Cleanup

```bash
make down
make clean
```
