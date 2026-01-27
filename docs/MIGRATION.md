# Phase 6 Migration - SBEN to S7BEN Naming Convention

**Migration Date:** January 21, 2026
**Status:** ✅ Complete
**Benchmarks Migrated:** 44

---

## Overview

Phase 6 of the Strike7 project involved a comprehensive infrastructure cleanup and renaming of all benchmarks from the `SBEN-*` format to the new `S7BEN-*` format to better reflect the Strike7 brand and provide clearer categorization.

---

## Changes Made

### 1. Benchmark Renaming

All 44 benchmarks were renamed according to the new naming convention:

**Format:** `S7BEN-{CATEGORY}-{NUMBER}`

| Category | Range | Old Format | Description |
|----------|-------|------------|-------------|
| EASY | 001-099 | SBEN-X00-0X | Training tier (hints allowed) |
| MED | 100-199 | SBEN-X00-T2 | Evaluation tier (no hints) |
| HARD | 200-299 | SBEN-HARD-XX, SBEN-XXX-T3 | Adversarial tier (defenses) |
| VHARD | 300-399 | SBEN-CHAIN-*, SBEN-AD-*, etc. | Multi-container chains |
| CVE | 400-499 | SBEN-CVE-XX | Real CVE reproductions |

### 2. Flag Format Update

All flags were updated from `SBEN{...}` to `S7BEN{...}` format:
- **Files Updated:** 335+ references across all benchmarks
- **File Types:** `*.yaml`, `*.py`, `*.md`, `*.sh`, `*.env`, `*.json`, `*.txt`
- **Remaining SBEN{:** 0

### 3. Documentation Cleanup

**Deleted (22 files):**
- `ALL_FIXES_COMPLETE.md`
- `ALL_ISSUES_RESOLVED.md`
- `BENCHMARKS_COMPLETED.md`
- `BENCHMARK_SCAFFOLDS_SUMMARY.md`
- `FINAL_FIXES_APPLIED.md`
- `FINAL_FIXES_COMPLETE.md`
- `FIXED_AND_READY.md`
- `ISSUES_FIXED_SUMMARY.md`
- `PHASE5_FINAL_STATUS.md`
- `PHASE5_FIXES_FINAL.md`
- `PHASE5_SETUP_COMMANDS.md`
- `REMAINING_ISSUES_SUMMARY.md`
- `SBEN-CVE-01_FIX.md`
- `READY_TO_TEST.md`
- `VERIFY_FIXES.sh`
- `REBUILD_AND_TEST.sh`
- `REBUILD_CVE03.sh`
- `FIX_CVE03_FINAL.sh`
- `FIX_HARD04.sh`
- `TEST_FINAL_TWO.sh`
- `TEST_HARD04_FINAL.sh`
- `TEST_HARD04_MANUAL.sh`

**Organized (moved to docs/):**
- `PHASE_2_PROGRESS.md`
- `PHASE4_COMPLETION.md`
- `PHASE5_COMPLETE.md`
- `PHASE6_STRIKE7_PLAN_v2.md`

**Kept in Root:**
- `README.md`
- `QUICKSTART.md`
- `START_HERE.txt`

### 4. Scripts Organization

All utility scripts moved to `scripts/` directory:
- `manage-containers.sh`
- `count-benchmarks.sh` (new)
- `cleanup-scattered-files.sh` (new)
- `rename-benchmarks.sh` (new)
- `update-flag-format.sh` (new)
- `verify-sample-benchmarks.sh` (new)

---

## Complete Benchmark Mapping

### EASY Tier (9 benchmarks)

| New ID | Old ID | Name |
|--------|--------|------|
| S7BEN-EASY-001 | SBEN-100-01 | CSRF - Password Change |
| S7BEN-EASY-002 | SBEN-200-01 | Hardcoded Secrets - API Key |
| S7BEN-EASY-003 | SBEN-400-01 | Race Condition - Balance Bypass |
| S7BEN-EASY-004 | SBEN-400-02 | Workflow Bypass - Order Status |
| S7BEN-EASY-005 | SBEN-900-01 | Insufficient Logging |
| S7BEN-EASY-006 | SBEN-900-02 | Log Injection |
| S7BEN-EASY-007 | SBEN-900-03 | Log Injection Variant |
| S7BEN-EASY-008 | SBEN-1010-T1 | Multi-Stage Auth Basic |
| S7BEN-EASY-009 | SBEN-300-T1 | Supply Chain Basic |

### MED Tier (12 benchmarks)

| New ID | Old ID | Name |
|--------|--------|------|
| S7BEN-MED-001 | SBEN-700-01 | Session Fixation |
| S7BEN-MED-002 | SBEN-400-03 | TOCTOU File Operation |
| S7BEN-MED-003 | SBEN-510-T2 | SQL Injection Evaluation |
| S7BEN-MED-004 | SBEN-520-T2 | XSS Evaluation |
| S7BEN-MED-005 | SBEN-110-T2 | IDOR Evaluation |
| S7BEN-MED-006 | SBEN-910-T2 | Log Chain Evaluation |
| S7BEN-MED-007 | SBEN-700-02 | Session Management Variant |
| S7BEN-MED-008 | SBEN-700-25 | Session Variant 2 |
| S7BEN-MED-009 | SBEN-500-01 | Security Misconfiguration |
| S7BEN-MED-010 | SBEN-1000-01 | SSRF Basic |
| S7BEN-MED-011 | SBEN-1010-T2 | Multi-Stage Auth Evaluation |
| S7BEN-MED-012 | SBEN-300-T2 | Supply Chain Evaluation |

### HARD Tier (8 benchmarks)

| New ID | Old ID | Name |
|--------|--------|------|
| S7BEN-HARD-001 | SBEN-HARD-01 | SQL Injection + ModSecurity WAF Bypass |
| S7BEN-HARD-002 | SBEN-HARD-02 | XSS + DOMPurify Bypass |
| S7BEN-HARD-003 | SBEN-HARD-03 | SSRF + Request Filtering |
| S7BEN-HARD-004 | SBEN-HARD-04 | JWT Auth Bypass + Rate Limiting |
| S7BEN-HARD-010 | SBEN-510-T3 | SQL Injection Adversarial |
| S7BEN-HARD-011 | SBEN-520-T3 | XSS + CSP Adversarial |
| S7BEN-HARD-012 | SBEN-110-T3 | IDOR Adversarial |
| S7BEN-HARD-013 | SBEN-910-T3 | Log Chain Adversarial |

### VHARD Tier (10 benchmarks)

| New ID | Old ID | Name |
|--------|--------|------|
| S7BEN-VHARD-001 | SBEN-CHAIN-01 | Microservices Exploitation Chain |
| S7BEN-VHARD-002 | SBEN-SSRF-01 | Advanced SSRF Filter Bypass |
| S7BEN-VHARD-003 | SBEN-AD-01 | Active Directory Kerberos Exploitation |
| S7BEN-VHARD-004 | SBEN-DESER-01 | Java Deserialization RCE |
| S7BEN-VHARD-005 | SBEN-DESER-02 | Python Pickle Deserialization |
| S7BEN-VHARD-006 | SBEN-GQL-01 | GraphQL Introspection to SQLi |
| S7BEN-VHARD-007 | SBEN-XXE-01 | XXE Out-of-Band Exfiltration |
| S7BEN-VHARD-008 | SBEN-NOSQL-01 | MongoDB Injection Chain |
| S7BEN-VHARD-009 | SBEN-SSTI-01 | Server-Side Template Injection Chain |
| S7BEN-VHARD-010 | SBEN-LFI-01 | Local File Inclusion to RCE Chain |

### CVE Tier (5 benchmarks)

| New ID | Old ID | Name | CVE |
|--------|--------|------|-----|
| S7BEN-CVE-001 | SBEN-CVE-01 | Apache HTTP Server Path Traversal | CVE-2021-41773 |
| S7BEN-CVE-002 | SBEN-CVE-02 | Apache Commons Text4Shell | CVE-2022-42889 |
| S7BEN-CVE-003 | SBEN-CVE-03 | Apache Log4Shell JNDI Injection | CVE-2021-44228 |
| S7BEN-CVE-004 | SBEN-CVE-04 | Spring Framework Spring4Shell | CVE-2022-22965 |
| S7BEN-CVE-005 | SBEN-CVE-05 | GitLab ExifTool RCE | CVE-2021-22205 |

---

## Directory Structure (After Migration)

```
strike7-benchmarks/
├── README.md                    # Main overview (updated)
├── QUICKSTART.md                # Quick start guide (updated)
├── START_HERE.txt               # First-time setup
│
├── docs/                        # All phase documentation
│   ├── PHASE_2_PROGRESS.md
│   ├── PHASE4_COMPLETION.md
│   ├── PHASE5_COMPLETE.md
│   ├── PHASE6_STRIKE7_PLAN_v2.md
│   └── MIGRATION.md             # This file
│
├── scripts/                     # Utility scripts
│   ├── count-benchmarks.sh
│   ├── cleanup-scattered-files.sh
│   ├── rename-benchmarks.sh
│   ├── update-flag-format.sh
│   ├── verify-sample-benchmarks.sh
│   └── manage-containers.sh
│
├── dashboard/                   # Flask dashboard
│   ├── config/
│   │   └── benchmarks.yaml      # Complete benchmark registry
│   ├── static/
│   └── templates/
│
├── docker-base-images/          # Reusable base images
│   ├── base-web-app/
│   ├── base-db/
│   ├── base-java-vuln/
│   ├── base-modsec-waf/
│   └── base-exploit-server/
│
└── benchmarks/                  # ALL benchmarks (S7BEN-* naming)
    ├── S7BEN-EASY-001/
    ├── S7BEN-EASY-002/
    ├── ...
    ├── S7BEN-MED-001/
    ├── ...
    ├── S7BEN-HARD-001/
    ├── ...
    ├── S7BEN-VHARD-001/
    ├── ...
    └── S7BEN-CVE-001/
```

---

## Verification

### Automated Verification

```bash
# Run verification script
./scripts/verify-sample-benchmarks.sh
```

**Results:**
- ✅ All 10 sample benchmarks passed verification
- ✅ Flag format updated to S7BEN{...}
- ✅ Directory structure correct
- ⚠ Some historical SBEN- references remain in documentation (acceptable)

### Manual Checks

```bash
# Count benchmarks
./scripts/count-benchmarks.sh

# Check for old SBEN{ flags (should return nothing)
grep -r "SBEN{" benchmarks/ --include="*.py" --include="*.yaml"

# Check for new S7BEN{ flags (should return many)
grep -r "S7BEN{" benchmarks/ --include="*.py" --include="*.yaml" | wc -l
```

---

## Impact Assessment

### What Changed
- ✅ All benchmark directory names
- ✅ All flag formats
- ✅ All internal references in code files
- ✅ Documentation (README, QUICKSTART)
- ✅ Dashboard configuration

### What Stayed the Same
- ✅ Docker container functionality
- ✅ Exploit techniques
- ✅ Difficulty levels
- ✅ OWASP categorization
- ✅ Makefile targets (`make up`, `make down`, `make test`)
- ✅ Port mappings
- ✅ Health check endpoints

---

## Usage Examples

### Old Way (SBEN)
```bash
cd benchmarks/SBEN-400-01
make up
curl http://localhost:5000/flag
# Flag: SBEN{r4c3_c0nd1t10n_m4st3r}
```

### New Way (S7BEN)
```bash
cd benchmarks/S7BEN-EASY-003
make up
curl http://localhost:5000/flag
# Flag: S7BEN{r4c3_c0nd1t10n_m4st3r}
```

---

## Backward Compatibility

⚠️ **Breaking Change:** This is a breaking change. Any external scripts or tools referencing `SBEN-*` naming will need to be updated.

**Migration for External Tools:**
```bash
# Update your scripts
sed -i 's/SBEN-100-01/S7BEN-EASY-001/g' your-script.sh
sed -i 's/SBEN{/S7BEN{/g' your-code.py
```

---

## Rollback Procedure

If rollback is needed:

```bash
# Restore from backup (created during flag update)
cd ~/workspace/strike7-benchmarks
tar -xzf benchmarks-backup-YYYYMMDD-HHMMSS.tar.gz

# Or use git if changes were committed
git revert <commit-hash>
```

---

## Next Steps (Phase 6B)

With infrastructure cleanup complete, the next phase involves:

1. **Add 20 New Benchmarks** to reach 64 total
   - Auth vulnerabilities (2FA bypass, OAuth, etc.)
   - Business logic flaws
   - Additional CVEs (2023-2025)
   - Misconfiguration scenarios

2. **Dashboard Enhancement**
   - Integrate with `dashboard/config/benchmarks.yaml`
   - Add benchmark search/filter UI
   - Telemetry visualization

3. **Continuous Expansion** towards 108 benchmarks (XBOW match)

---

## References

- Phase 6 Master Plan: `docs/PHASE6_STRIKE7_PLAN_v2.md`
- Phase 5 Completion: `docs/PHASE5_COMPLETE.md`
- Phase 4 Completion: `docs/PHASE4_COMPLETION.md`
- Dashboard Registry: `dashboard/config/benchmarks.yaml`

---

**Migration completed successfully on January 21, 2026 ✅**
