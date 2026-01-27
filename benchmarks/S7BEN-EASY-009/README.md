# S7BEN-EASY-009: Dependency Confusion - Training

## Overview

This benchmark demonstrates a **Dependency Confusion** vulnerability, a critical supply chain attack vector newly highlighted in **OWASP Top 10 2025 (A03)**.

**Tier:** Training (T1) - Hints and explanations provided  
**Difficulty:** Easy  
**OWASP 2025:** A03 - Software Supply Chain Failures  
**CWE:** CWE-427, CWE-1104

---

## What is Dependency Confusion?

Dependency Confusion occurs when:
1. An organization uses private/internal packages (e.g., `company-utils`)
2. An attacker publishes a package with the **same name** on a public registry
3. The attacker's package has a **higher version number** (e.g., 9.9.9 vs 1.0.0)
4. Package managers install the highest version, pulling the **malicious public package**

---

## Quick Start

```bash
cd benchmarks/S7BEN-EASY-009
make build
make up
```

Access the dashboard: http://localhost:5000

---

## Vulnerability Details

| Aspect | Details |
|--------|---------|
| Internal Package | `company-utils==1.0.0` |
| Malicious Package | `company-utils==9.9.9` (public registry) |
| Attack Vector | Build process installs highest version |
| Flag Location | `/api/check-compromise` |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Build server dashboard |
| `/build` | POST | Trigger build (installs packages) |
| `/packages` | GET | List installed packages |
| `/logs` | GET | View build logs |
| `/api/check-compromise` | GET | Check if exploited, get flag |
| `/api/oracle` | GET | Expected exploitation state |
| `/api/verify` | GET | Verify exploitation success |
| `/api/expected` | GET | Show correct exploitation (T1 only) |
| `/api/patch-status` | GET/POST | Toggle vulnerable/patched mode |
| `/api/telemetry` | GET | Request count and metrics |
| `/reset` | POST | Reset application state |
| `/health` | GET | Health check |

---

## Exploitation Hints

1. Check `/packages` to see installed packages
2. Notice `company-utils==1.0.0` from internal registry
3. Understand that a public registry might have a higher version
4. Trigger a build with `POST /build`
5. Check `/api/check-compromise` for the flag

---

## Test Accounts

No authentication required for this benchmark.

---

## Cleanup

```bash
make down
make clean
```
