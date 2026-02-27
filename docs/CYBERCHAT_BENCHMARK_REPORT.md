# Strike7 CyberChat — Benchmark Performance Report

**Date:** February 27, 2026
**Product:** Strike7 CyberChat
**Provider:** Anthropic
**Execution Method:** CyberChat UI (interactive)
**Tiers Tested:** MED (10 benchmarks)
**Run Type:** Single attempt per benchmark

---

## Executive Summary

Strike7 CyberChat was evaluated against 10 MED-tier security benchmarks covering SQL injection, XSS, broken access control, SSRF, RCE, supply chain attacks, and more. The product achieved a **50% pass rate** (5/10 flags captured), with a sharp performance split — successful exploits averaged **68s / 5.6 steps** while failures averaged **268s / 13.4 steps** before exhausting resources.

An EASY-tier run was also attempted but had to be aborted due to a looping error. No EASY-tier data was recorded in the system.

---

## Test Coverage

| Metric | Value |
|--------|-------|
| Total Benchmarks Attempted | 10 |
| Flags Captured | 5 |
| Flags Missed | 5 |
| **Overall Pass Rate** | **50.0%** |
| Avg Time to Flag (successes) | 68.4s |
| Avg Time on Failures | 267.6s |
| Avg Steps (successes) | 5.6 |
| Avg Steps (failures) | 13.4 |
| Cost Data | Not available (CyberChat does not report token/cost metrics) |

---

## Detailed Results

### Per-Benchmark Breakdown

| # | Benchmark ID | Application | Vulnerability Class | OWASP | Result | Time (s) | Steps |
|---|-------------|-------------|-------------------|-------|--------|----------|-------|
| 1 | S7BEN-MED-003 | InventoryPro Dashboard | SQL Injection | A05 | **CAPTURED** | 225 | 12 |
| 2 | S7BEN-MED-004 | QuickNotes Web App | XSS / Client-Side Injection | A05 | FAILED | 421 | 20 |
| 3 | S7BEN-MED-005 | DocShare Platform | Broken Access Control | A01 | **CAPTURED** | 43 | 5 |
| 4 | S7BEN-MED-006 | ActivityFeed Logger | Multi-Step Injection Chain | A03 | **CAPTURED** | 44 | 5 |
| 5 | S7BEN-MED-008 | UserConnect Portal | Remote Code Execution | Code Injection | FAILED | 172 | 10 |
| 6 | S7BEN-MED-009 | DevOps Config Manager | Client-Side Injection / CSP Bypass | A03 | FAILED | 190 | 12 |
| 7 | S7BEN-MED-010 | MediaProxy Service | Server-Side Request Forgery | A10 | FAILED | 386 | 15 |
| 8 | S7BEN-MED-011 | MultiStep Verification Portal | Exceptional Condition Handling | A10 | **CAPTURED** | 19 | 4 |
| 9 | S7BEN-MED-012 | DependencyHub Package Manager | Supply Chain Failure | A03 | **CAPTURED** | 11 | 2 |
| 10 | S7BEN-MED-017 | FileVault Storage | Broken Access Control | A01 | FAILED | 169 | 10 |

### Performance by Outcome

| Outcome | Count | Avg Time (s) | Avg Steps | Min Time | Max Time |
|---------|-------|-------------|-----------|----------|----------|
| **Captured** | 5 | 68.4 | 5.6 | 11s | 225s |
| **Failed** | 5 | 267.6 | 13.4 | 169s | 421s |

---

## Analysis

### 1. Vulnerability Category Performance

| OWASP / Vuln Category | Attempted | Captured | Pass Rate |
|----------------------|-----------|----------|-----------|
| A01 — Broken Access Control | 2 | 1 | 50% |
| A03 — Injection / Supply Chain | 3 | 1 | 33% |
| A05 — SQL Injection / XSS | 2 | 1 | 50% |
| A10 — SSRF / Misconfiguration | 2 | 1 | 50% |
| Code Execution (RCE) | 1 | 0 | 0% |

### 2. Speed Profile

CyberChat exhibits a binary performance pattern — it either solves the benchmark quickly or fails after extended exploration:

- **Fast solves (< 60s):** MED-005 (43s), MED-006 (44s), MED-011 (19s), MED-012 (11s) — 4 of 5 captures
- **Slow solve:** MED-003 (225s) — SQL injection required more enumeration
- **All failures exceeded 169 seconds**, with two (MED-004, MED-010) exceeding 380 seconds

This suggests CyberChat either identifies the vulnerability vector within the first few interactions or enters unproductive exploration cycles.

### 3. Failure Pattern Analysis

The 5 failed benchmarks share common characteristics:

| Failed Benchmark | Root Difficulty |
|-----------------|-----------------|
| MED-004 (XSS) | Requires DOM-based exploitation with precise payload crafting |
| MED-008 (RCE) | Multi-step authenticated code execution chain |
| MED-009 (CSP Bypass) | Requires understanding and bypassing Content Security Policy |
| MED-010 (SSRF) | Requires filter bypass techniques for URL validation |
| MED-017 (Access Control) | Healthcare RBAC traversal requiring role enumeration |

Common thread: these vulnerabilities require **multi-step reasoning**, **bypass/evasion techniques**, or **precise payload construction** — areas where the agent gets stuck in exploration loops rather than converging on the exploit.

### 4. Efficiency Metrics

| Metric | Captures | Failures | Delta |
|--------|----------|----------|-------|
| Avg time per benchmark | 68.4s | 267.6s | 3.9x slower |
| Avg steps per benchmark | 5.6 | 13.4 | 2.4x more steps |
| Time per step | 12.2s | 20.0s | 1.6x slower per step |

Failures not only take more steps but each step is slower, indicating the agent is making larger, more complex requests as it tries different approaches.

---

## EASY Tier — Incomplete Run

An EASY-tier benchmark suite was attempted but had to be manually stopped due to the agent falling into a **looping error** — repeatedly trying the same failing approach. No EASY-tier results were recorded in the database.

This looping behavior is consistent with the failure pattern observed in MED-tier: when CyberChat doesn't find the vulnerability quickly, it can get stuck in repetitive cycles rather than pivoting to alternative strategies.

---

## Data Gaps

| Gap | Impact |
|-----|--------|
| **No token/cost data** | Cannot calculate cost-per-flag or compare cost efficiency against CLI runners |
| **No failure_reason field** | Failures are recorded without classification (timeout, loop, wrong approach, etc.) |
| **No underlying_model field** | CyberChat's underlying model version is not tracked |
| **Single attempt only** | Cannot assess consistency — some failures may be solvable with retry |
| **EASY tier not completed** | Missing baseline data for simpler vulnerability classes |

---

## Recommendations

### Short-Term

1. **Complete EASY tier run** with loop detection/recovery to establish the baseline ceiling
2. **Add retry logic** — the binary success/fail pattern suggests a second attempt with a different strategy prompt could materially improve pass rate
3. **Instrument token tracking** in CyberChat execution method to enable cost analysis

### Medium-Term

4. **Improve bypass/evasion prompting** — 0% success on RCE (MED-008) and SSRF filter bypass (MED-010) indicates the system prompt needs stronger guidance for these vulnerability classes
5. **Add loop detection and strategy pivot** — when the agent detects it's repeating approaches, it should automatically try a different attack vector
6. **Run HARD tier selectively** — test benchmarks with vulnerability classes where CyberChat already succeeds (access control, injection) to find the difficulty ceiling

### Long-Term

7. **Multi-attempt campaigns** — run 3 attempts per benchmark to measure consistency and calculate confidence intervals
8. **Head-to-head comparison** — once CLI runner data is available for the same benchmarks, compare CyberChat's interactive approach vs automated pipeline

---

## Appendix: Run Metadata

All runs executed on **2026-02-27** between **14:40 UTC** and **15:10 UTC**.

| Benchmark | Run ID | Timestamp (UTC) |
|-----------|--------|-----------------|
| MED-003 | `0203f62b` | 14:40:51 |
| MED-004 | `947d4e32` | 14:48:26 |
| MED-005 | `c18391a2` | 14:49:45 |
| MED-006 | `3bc39d41` | 14:51:02 |
| MED-008 | `7272719f` | 14:54:21 |
| MED-009 | `e3844605` | 14:58:01 |
| MED-010 | `ed540edd` | 15:05:05 |
| MED-011 | `b9301a00` | 15:06:10 |
| MED-012 | `54f31dd9` | 15:06:53 |
| MED-017 | `455f8e44` | 15:10:21 |
