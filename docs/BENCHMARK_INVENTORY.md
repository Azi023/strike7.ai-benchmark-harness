# Strike7 Benchmark Inventory

**Last Updated:** 2026-01-22
**Total Benchmarks:** 64
**Target:** 108 (44 more needed)

---

## Summary Statistics

| Category | Count | Percentage |
|----------|-------|------------|
| EASY | 9 | 14% |
| MED | 16 | 25% |
| HARD | 14 | 22% |
| VHARD | 14 | 22% |
| CVE | 11 | 17% |
| **TOTAL** | **64** | **100%** |

---

## Breakdown by Phase

| Phase | Benchmarks | Description |
|-------|-----------|-------------|
| Phase 1 | 6 | Easy tier training benchmarks |
| Phase 2-3 | 12 | MED/HARD evaluation benchmarks |
| Phase 4 | 10 | VHARD multi-container chains |
| Phase 5 | 16 | HARD tier + initial CVEs |
| **Phase 6B** | **20** | **New auth, business logic, misconfig, CVE benchmarks** |
| **Total** | **64** | |

---

## OWASP 2025 Coverage

| OWASP Category | Benchmark Count |
|----------------|----------------|
| A01 - Broken Access Control | 14 |
| A02 - Cryptographic Failures | 4 |
| A03 - Injection | 19 |
| A04 - Insecure Design | 7 |
| A05 - Security Misconfiguration | 8 |
| A06 - Vulnerable Components | 11 |
| A07 - Authentication Failures | 11 |
| A08 - Software Data Integrity Failures | 8 |
| A09 - Security Logging Failures | 2 |
| A10 - SSRF | 5 |

*Note: Some benchmarks cover multiple OWASP categories*

---

## Complete Benchmark List

### EASY Tier (9 benchmarks)

| ID | Name | OWASP | Port | Phase |
|----|------|-------|------|-------|
| S7BEN-EASY-001 | CSRF - Password Change | A01 | 5000 | 1 |
| S7BEN-EASY-002 | Hardcoded Secrets - API Key | A02 | 5000 | 1 |
| S7BEN-EASY-003 | Race Condition - Balance Bypass | A04 | 5000 | 1 |
| S7BEN-EASY-004 | Workflow Bypass | A04 | 5000 | 1 |
| S7BEN-EASY-005 | Insufficient Logging | A09 | 5000 | 1 |
| S7BEN-EASY-006 | Log Injection | A09 | 5000 | 1 |
| S7BEN-EASY-007 | SQL Injection - Basic | A03 | 5000 | 1 |
| S7BEN-EASY-008 | XSS - Reflected | A03 | 5000 | 1 |
| S7BEN-EASY-009 | Path Traversal | A01 | 5000 | 1 |

---

### MED Tier (16 benchmarks)

| ID | Name | OWASP | Port | Phase |
|----|------|-------|------|-------|
| S7BEN-MED-001 | JWT Algorithm Confusion | A07 | 8080 | 2 |
| S7BEN-MED-002 | XML External Entity (XXE) | A03 | 8080 | 2 |
| S7BEN-MED-003 | Server-Side Request Forgery (SSRF) | A10 | 8080 | 2 |
| S7BEN-MED-004 | NoSQL Injection | A03 | 8080 | 2 |
| S7BEN-MED-005 | Directory Traversal Advanced | A01 | 8080 | 2 |
| S7BEN-MED-006 | Command Injection | A03 | 8080 | 3 |
| S7BEN-MED-007 | IDOR - Insecure Direct Object Reference | A01 | 8080 | 3 |
| S7BEN-MED-008 | Mass Assignment | A01 | 8080 | 3 |
| S7BEN-MED-009 | Open Redirect | A01 | 8080 | 3 |
| S7BEN-MED-010 | Rate Limiting Bypass | A07 | 8080 | 3 |
| S7BEN-MED-011 | GraphQL Introspection | A05 | 8080 | 5 |
| S7BEN-MED-012 | API Key Enumeration | A07 | 8080 | 5 |
| **S7BEN-MED-013** | **Weak Password Policy** | **A07** | **8099** | **6B** |
| **S7BEN-MED-014** | **Coupon Code Reuse** | **A04** | **8100** | **6B** |
| **S7BEN-MED-015** | **Flask Debug Mode in Production** | **A05** | **8103** | **6B** |
| **S7BEN-MED-016** | **Default Credentials** | **A05** | **8104** | **6B** |

---

### HARD Tier (14 benchmarks)

| ID | Name | OWASP | Port | Phase |
|----|------|-------|------|-------|
| S7BEN-HARD-001 | Blind SQL Injection | A03 | 8001 | 3 |
| S7BEN-HARD-002 | Blind XSS | A03 | 8002 | 3 |
| S7BEN-HARD-003 | Second-Order SQL Injection | A03 | 8003 | 3 |
| S7BEN-HARD-004 | SSRF with Blacklist Bypass | A10 | 8004 | 3 |
| S7BEN-HARD-010 | Prototype Pollution | A08 | 8010 | 5 |
| S7BEN-HARD-011 | JWT Key Confusion | A07 | 8011 | 5 |
| S7BEN-HARD-012 | SSTI - Template Injection | A03 | 8012 | 5 |
| S7BEN-HARD-013 | GraphQL Batching Attack | A05 | 8013 | 5 |
| **S7BEN-HARD-014** | **Password Reset Token Reuse** | **A07** | **8093** | **6B** |
| **S7BEN-HARD-015** | **Session Fixation via Cookie Injection** | **A07** | **8094** | **6B** |
| **S7BEN-HARD-016** | **Workflow State Manipulation** | **A04** | **8097** | **6B** |
| **S7BEN-HARD-017** | **Client-Side Price Manipulation** | **A04** | **8098** | **6B** |
| **S7BEN-HARD-018** | **Kubernetes RBAC Privilege Escalation** | **A05** | **8101** | **6B** |
| **S7BEN-HARD-019** | **Docker Socket Exposure Container Escape** | **A05** | **8102** | **6B** |

---

### VHARD Tier (14 benchmarks)

| ID | Name | OWASP | Port | Containers | Phase |
|----|------|-------|------|------------|-------|
| S7BEN-VHARD-001 | Microservices Exploitation Chain | A01 | 8020 | 6 | 4 |
| S7BEN-VHARD-002 | Advanced SSRF Filter Bypass | A10 | 8021 | 4 | 4 |
| S7BEN-VHARD-003 | Active Directory Kerberos Exploitation | A07 | 8022 | 5 | 4 |
| S7BEN-VHARD-004 | Java Deserialization RCE | A08 | 8023 | 3 | 4 |
| S7BEN-VHARD-005 | Python Pickle Deserialization | A08 | 8024 | 3 | 4 |
| S7BEN-VHARD-006 | GraphQL Introspection to SQLi | A03 | 8025 | 2 | 4 |
| S7BEN-VHARD-007 | XXE Out-of-Band Exfiltration | A03 | 8026 | 3 | 4 |
| S7BEN-VHARD-008 | MongoDB Injection Chain | A03 | 8027 | 3 | 4 |
| S7BEN-VHARD-009 | Server-Side Template Injection Chain | A03 | 8028 | 3 | 4 |
| S7BEN-VHARD-010 | Local File Inclusion to RCE Chain | A03 | 8029 | 3 | 4 |
| **S7BEN-VHARD-011** | **2FA Session State Bypass** | **A07** | **8087** | **1** | **6B** |
| **S7BEN-VHARD-012** | **OAuth State Parameter Confusion** | **A07** | **8091** | **2** | **6B** |
| **S7BEN-VHARD-013** | **Race Condition Double Spend** | **A04** | **8095** | **1** | **6B** |
| **S7BEN-VHARD-014** | **Negative Quantity Business Logic Bypass** | **A04** | **8096** | **1** | **6B** |

---

### CVE Tier (11 benchmarks)

| ID | Name | CVE | CVSS | Year | Port | Phase |
|----|------|-----|------|------|------|-------|
| S7BEN-CVE-001 | Apache Struts RCE | CVE-2017-5638 | 10.0 | 2017 | 8030 | 5 |
| S7BEN-CVE-002 | Log4Shell RCE | CVE-2021-44228 | 10.0 | 2021 | 8031 | 5 |
| S7BEN-CVE-003 | Spring4Shell RCE | CVE-2022-22965 | 9.8 | 2022 | 8032 | 5 |
| S7BEN-CVE-004 | ProxyShell Exchange RCE | CVE-2021-34473 | 9.8 | 2021 | 8033 | 5 |
| S7BEN-CVE-005 | ProxyLogon Exchange RCE | CVE-2021-26855 | 9.1 | 2021 | 80 | 5 |
| **S7BEN-CVE-006** | **runc Container Escape** | **CVE-2024-21626** | **8.6** | **2024** | **8105** | **6B** |
| **S7BEN-CVE-007** | **HTTP/2 Rapid Reset DoS** | **CVE-2023-44487** | **7.5** | **2023** | **8106** | **6B** |
| **S7BEN-CVE-008** | **PAN-OS Command Injection** | **CVE-2024-3400** | **10.0** | **2024** | **8107** | **6B** |
| **S7BEN-CVE-009** | **Confluence Privilege Escalation** | **CVE-2023-22515** | **9.8** | **2023** | **8108** | **6B** |
| **S7BEN-CVE-010** | **TeamCity Auth Bypass** | **CVE-2024-27198** | **9.8** | **2024** | **8109** | **6B** |
| **S7BEN-CVE-011** | **ActiveMQ Deserialization RCE** | **CVE-2023-46604** | **10.0** | **2023** | **8110** | **6B** |

---

## Port Allocation

| Range | Category | Count | Phase |
|-------|----------|-------|-------|
| 5000 | EASY (shared) | 9 | 1 |
| 8080 | MED (shared) | 12 | 2-3, 5 |
| 8001-8004 | HARD (early) | 4 | 3 |
| 8010-8013 | HARD (later) | 4 | 5 |
| 8020-8029 | VHARD (Phase 4) | 10 | 4 |
| 8030-8033, 80 | CVE (Phase 5) | 5 | 5 |
| **8087, 8091-8110** | **Phase 6B** | **20** | **6B** |

**Total Ports Used:** 34 unique ports

---

## Difficulty Distribution

```
EASY (1-3):     █████████                     9 benchmarks  (14%)
MED (4-6):      ████████████████             16 benchmarks  (25%)
HARD (7-8):     ██████████████               14 benchmarks  (22%)
VHARD (9):      ██████████████               14 benchmarks  (22%)
CVE (varies):   ███████████                  11 benchmarks  (17%)
```

---

## Phase 6B Additions (January 2026)

**New Benchmarks:** 20
**Categories Covered:** 4 (Auth, Business Logic, Misconfiguration, CVE)
**Difficulty Range:** MED to VHARD (5-9)

### Key Features
✅ All use dynamic flag generation
✅ Full telemetry integration
✅ CLI-exploitable (curl/Python)
✅ Comprehensive documentation
✅ OWASP 2025 mapped
✅ CWE classified

---

## Future Phases

**Remaining to 108 Target:** 44 benchmarks

**Planned Categories:**
- API Security (REST, GraphQL, gRPC)
- Cloud Security (AWS, Azure, GCP)
- Container Security (K8s, Docker advanced)
- Mobile Backend Vulnerabilities
- Cryptographic Attacks
- Advanced Persistence Mechanisms

---

*Inventory maintained by Strike7 Security Team*
*For detailed benchmark info, see individual benchmark.yaml files*
