# Strike7 Benchmark Audit — Consolidated Findings & Action Plan

> **Date:** 2026-02-26  
> **Audited by:** Gemini Agent (4 parallel prompts across all tiers)  
> **Compiled by:** Atheeque / Claude Opus  
> **Total Benchmarks:** 67 (Local) | Sync confirmed with VPS  
> **Git:** main branch, commit `d44e726` ("fix: harden HARD-tier benchmarks")

---

## 1. SYNC CHECK RESULTS

The sync-check script confirmed **local and VPS are in sync** with two minor differences:

| Item | Local | VPS | Impact |
|------|-------|-----|--------|
| Dirty files | 84 uncommitted | 0 (clean) | Local has pending changes — commit or stash |
| VHARD-003 port | 5072 | 389 | **CRITICAL** — VPS docker-compose was manually edited to use LDAP port 389. Local still says 5072. CI/CD won't fix this because VPS has a manual override. |

**Fix:** Either update local docker-compose for VHARD-003 to port 389 (correct for Active Directory/LDAP), or standardize on 5072 and update VPS. Since VHARD-003 is the AD/Kerberos benchmark, port 389 (LDAP) is actually correct — update local to match.

```bash
# On LOCAL — fix the port mismatch
cd ~/workspace/strike7-benchmarks/benchmarks/S7BEN-VHARD-003
# Edit docker-compose.yml to use port 389 instead of 5072
sed -i 's/5072/389/g' docker-compose.yml
git add docker-compose.yml
git commit -m "fix: align VHARD-003 port to 389 (LDAP) matching VPS"

# Then commit your 84 dirty files
cd ~/workspace/strike7-benchmarks
git add -A
git status  # Review what's being committed
git commit -m "chore: sync local with VPS state"
git push
```

---

## 2. CROSS-TIER FINDINGS SUMMARY

### 2.1 Overall Health

| Tier | Audited | 🟢 Authentic | 🟡 Partial | 🔴 Simulated | ⚫ Broken | Start Rate |
|------|---------|-------------|-----------|-------------|----------|------------|
| EASY (21) | 21/21 | 10 | 4 | 7 | 0 | 100% |
| MED (18) | 6/18* | 3 | 0 | 3 | 0 | 100% |
| HARD (8) | 8/8 | 4 | 1 | 3 | 0 | 100% |
| VHARD (11) | 11/11 | 10 | 0 | 0 | 1† | 100% |
| CVE (9) | 9/9 | 7 | 1 | 1 | 0 | 100% |

*MED only 6 deeply audited — remaining 12 need follow-up  
†VHARD-015 not broken but misclassified (single-container prompt injection)

### 2.2 Identity Mismatches (The "RecoverID Problem")

These benchmarks have internal code/telemetry IDs that don't match their registry IDs:

| Registry ID | Internal/Telemetry ID | Original Tier | Current Tier | Action |
|-------------|----------------------|---------------|--------------|--------|
| S7BEN-EASY-010 | S7BEN-HARD-015 | HARD | EASY | **BROKEN** — needs bot or replacement |
| S7BEN-EASY-011 | S7BEN-HARD-016 | HARD | EASY | Update internal refs |
| S7BEN-EASY-012 | S7BEN-HARD-017 | HARD | EASY | Update internal refs |
| S7BEN-EASY-014 | S7BEN-HARD-019 | HARD | EASY | Update internal refs |
| S7BEN-EASY-016 | S7BEN-VHARD-014 | VHARD | EASY | Update internal refs |
| S7BEN-EASY-017 | S7BEN-VHARD-011 | VHARD | EASY | Update internal refs |
| S7BEN-MED-018 | S7BEN-HARD-014 | HARD | MED | Update internal refs |
| S7BEN-MED-019 | S7BEN-VHARD-013 | VHARD | MED | Update internal refs |

**Root Cause:** During Sprint 10's mass rename (66 benchmarks renamed to app-themed names), the source code telemetry strings, HTML templates, and README files were NOT updated — only the folder names, API registry, and docker-compose labels were changed.

### 2.3 Hint Contamination

| Tier | Contaminated | Clean | Details |
|------|-------------|-------|---------|
| EASY | 8 (38%) | 13 | Old tier IDs in HTML/telemetry leak original difficulty |
| MED | 2 (33% of audited) | 4 | MED-018 robots.txt leaks mailbox; MED-013 leaks usernames |
| HARD | 0 | 8 | Clean after Sprint 10 hardening |
| VHARD | 10 (91%) | 1 | YAML files expose vuln details; VHARD-009 names engines in UI |
| CVE | 0 | 9 | Clean — CVEs are public knowledge anyway |

### 2.4 Missing from API Registry

| Benchmark | On Disk? | In benchmarks.json? | Impact |
|-----------|----------|---------------------|--------|
| S7BEN-CVE-010 (TeamCity) | ✅ Yes | ❌ No | Invisible to agents via MCP |

---

## 3. RECLASSIFICATION MATRIX

### 3.1 Benchmarks That Must Move

| Current ID | Current Tier | Move To | Reason | Complexity Score |
|------------|-------------|---------|--------|-----------------|
| S7BEN-EASY-010 | EASY | **REMOVE or REBUILD** | Broken (needs victim bot, internally HARD-015) | N/A |
| S7BEN-EASY-014 | EASY | **REMOVE** | Flag dispenser — returns flag at /api/flag | 1/10 |
| S7BEN-EASY-018 | EASY | **MED or HARD** | CVE-2024-3400 PAN-OS simulation, too complex for EASY | 7/10 |
| S7BEN-EASY-019 | EASY | **Verify** | Needs audit (may need reclassification) | TBD |
| S7BEN-EASY-021 | EASY | **REMOVE** | Returns flag if "exploit" in POST body | 1/10 |
| S7BEN-MED-013 | MED | **EASY** | Simple brute force on 3 weak passwords | 3/10 |
| S7BEN-MED-001 | MED | **HARD** | Session fixation needs precise understanding + missing bot | 7/10 |
| S7BEN-MED-002 | MED | **HARD** | TOCTOU/Symlink race — extremely difficult for LLMs | 8/10 |
| S7BEN-MED-019 | MED | **HARD** | High-concurrency race condition | 8/10 |
| S7BEN-HARD-010 | HARD | **MED** | Single container, SQLite, only blind SQLi | 2/7 criteria |
| S7BEN-HARD-011 | HARD | **MED** | Single container, JSON storage, CSP bypass only | 2/7 criteria |
| S7BEN-HARD-013 | HARD | **MED** | Single container, mock DB, log injection to RCE | 2/7 criteria |
| S7BEN-VHARD-009 | VHARD | **REDESIGN** | Engine names in UI = critical hint contamination | 4/7 criteria |
| S7BEN-VHARD-015 | VHARD | **HARD** | Single container prompt injection, difficulty 4 | 3/7 criteria |

### 3.2 Safe Migration Procedure

**CRITICAL: When moving a benchmark between tiers, follow this checklist:**

```
For each benchmark being moved (e.g., MED-013 → EASY):

1. ASSIGN NEW ID
   - New ID follows the target tier's numbering: S7BEN-EASY-022 (next available)
   - NEVER reuse an old number in the original tier

2. RENAME FOLDER
   mv benchmarks/S7BEN-MED-013 benchmarks/S7BEN-EASY-022

3. UPDATE ALL INTERNAL REFERENCES (the mistake Sprint 10 made)
   Find and replace in ALL files within the benchmark folder:
   - app.py / server.js (telemetry strings, route prefixes)
   - HTML templates (any displayed IDs, page titles)
   - benchmark-config.json (id field, difficulty field)
   - docker-compose.yml (service names, container names, labels)
   - Makefile (if present)
   - README.md
   - Any test scripts referencing this benchmark

   grep -r "S7BEN-MED-013" benchmarks/S7BEN-EASY-022/
   # Replace ALL hits with S7BEN-EASY-022

4. UPDATE PORT
   - Assign port from target tier's range
   - EASY: 5001-5029 (find next unused)
   - MED: 5030-5049
   - HARD: 5050-5059
   - VHARD: 5070-5089
   - CVE: 5090-5099

5. UPDATE REGISTRY
   - Edit dashboard/data/benchmarks.json
   - Change: id, difficulty, port, name (if needed)
   - Remove the OLD entry entirely

6. UPDATE DIFFICULTY IN CONFIG
   - benchmark-config.json: "difficulty": "EASY"

7. VERIFY NO ORPHANS
   - grep -r "S7BEN-MED-013" . (from repo root)
   - Should return ZERO hits outside of git history

8. TEST
   docker compose build
   docker compose up -d
   curl http://localhost:<new-port>/
   docker compose down

9. COMMIT AS SINGLE ATOMIC CHANGE
   git add -A
   git commit -m "refactor: move S7BEN-MED-013 → S7BEN-EASY-022 (brute force too simple for MED)"
```

### 3.3 For Benchmarks Being REMOVED

```
1. Delete the folder
   rm -rf benchmarks/S7BEN-EASY-014

2. Remove from benchmarks.json
   Edit dashboard/data/benchmarks.json — delete the entry

3. Remove any test scripts
   grep -r "EASY-014" tests/ scripts/ — delete hits

4. Commit
   git add -A
   git commit -m "remove: S7BEN-EASY-014 (flag dispenser, no AI capability tested)"

5. DO NOT reassign the number
   EASY-014 is retired. Next EASY benchmark gets EASY-022 (or whatever is next unused)
```

---

## 4. SIMULATED SERVICES THAT MUST BE REPLACED

| Benchmark | Fake Service | What It Does Now | Replace With | Effort |
|-----------|-------------|-----------------|-------------|--------|
| MED-018 (RecoverID) | `/api/mailbox` Flask route | Python dict stores reset tokens | **MailHog container** (real SMTP + HTTP API) | Medium |
| MED-013 (AdminGate) | Hardcoded user dict | 3 passwords in a Python dict | **SQLite user table** with bcrypt hashes | Low |
| MED-019 (CryptoWallet) | `time.sleep` race sim | Simulated race on a dict | **Redis + actual concurrent transactions** | High |
| HARD-010 (DataSearch) | SQLite (acceptable) | Single container blind SQLi | Add **auth service container** to meet HARD standard | Medium |
| HARD-011 (ContentHub) | JSON file storage | Single container CSP bypass | Add **Redis session store** container | Medium |
| HARD-013 (LogAnalytics) | Mock dict DB | Single container log injection | Add **Elasticsearch container** for real log storage | High |
| MED-001 (TeamAuth) | No victim bot | Session fixation has no target | Add **Playwright/Puppeteer bot** container | Medium |
| EASY-010 (SessionTrack) | No victim bot | Session fixation impossible | Either add bot or **rebuild as simpler challenge** | Medium |

---

## 5. PORT CONFLICT & MAPPING ISSUES

| Benchmark | Issue | Fix |
|-----------|-------|-----|
| HARD-001 | Nginx listens on port 80 but Docker maps 5050:8080 | Change docker-compose to `5050:80` or nginx.conf to `listen 8080` |
| VHARD-003 | Local: 5072, VPS: 389 | Standardize on 389 (LDAP standard port) |
| CVE-010 | Not in benchmarks.json | Add entry to registry |
| MED-018 | Port 5046 correct but telemetry says HARD-014 | Fix telemetry string |

---

## 6. PRIORITY ACTION PLAN

### Phase 1: Critical Fixes (Do First — 1-2 hours)

```
Priority  | Task                                           | Effort
----------|------------------------------------------------|--------
P0        | Fix HARD-001 nginx port (5050:80)              | 5 min
P0        | Add CVE-010 to benchmarks.json                 | 5 min
P0        | Fix VHARD-003 port on local (389)              | 5 min
P0        | Commit 84 dirty local files                    | 10 min
P1        | Global grep+replace: fix all 8 identity        | 30 min
          | mismatches (telemetry strings in source code)   |
P1        | Scrub VHARD-009 hint contamination (UI titles)  | 15 min
P1        | Scrub VHARD YAML hint contamination (10 files)  | 30 min
```

### Phase 2: Reclassifications (Do Second — 2-3 hours)

Follow the Safe Migration Procedure in Section 3.2 for each:

```
Move  | From → To                    | New ID
------|------------------------------|------------------
1     | MED-013 → EASY               | S7BEN-EASY-022
2     | HARD-010 → MED               | S7BEN-MED-020
3     | HARD-011 → MED               | S7BEN-MED-021
4     | HARD-013 → MED               | S7BEN-MED-022
5     | MED-001 → HARD               | S7BEN-HARD-021
6     | MED-002 → HARD               | S7BEN-HARD-022
7     | MED-019 → HARD               | S7BEN-HARD-023
8     | VHARD-015 → HARD             | S7BEN-HARD-024
9     | EASY-018 → MED               | S7BEN-MED-023
```

**Removals:**
```
Remove | Benchmark    | Reason
-------|--------------|----------------------------------
1      | EASY-014     | Flag dispenser (/api/flag)
2      | EASY-021     | Flag if "exploit" in POST body
3      | EASY-010     | Broken (needs bot, internally HARD-015)
```

### Phase 3: Infrastructure Upgrades (Do Third — 1-2 days)

Replace simulated services with real ones (see Section 4).

### Phase 4: Remaining MED Audit (12 unaudited benchmarks)

The MED audit only covered 6/18. Run Prompt 2 again targeting the remaining 12 specifically.

---

## 7. POST-RECLASSIFICATION DISTRIBUTION

| Tier | Current | After Moves | After Removals | Target |
|------|---------|-------------|----------------|--------|
| EASY | 21 | 22 (+MED-013) | **19** (-014, -021, -010) | — |
| MED | 18 | 18 (+HARD-010,011,013, +EASY-018) (-MED-013, -001, -002, -019) | 18 | — |
| HARD | 8 | 8 (+MED-001,002,019, +VHARD-015) (-010,-011,-013) + net change | **12** | — |
| VHARD | 11 | 10 (-VHARD-015) | 10 | — |
| CVE | 9 | 9 | 9 | — |
| **TOTAL** | **67** | **67** | **64** (after 3 removals) | 108 (XBOW) |

Gap to 108: **44 more benchmarks needed**

---

## 8. DELEGATION PROMPT (for Claude Code / Codex)

Use this prompt to execute Phase 1 fixes:

```
CONTEXT: Strike7 AI benchmark platform. Sprint 12 infrastructure audit found 
critical issues. You are executing fixes on the LOCAL codebase at 
~/workspace/strike7-benchmarks/. CI/CD will deploy to VPS automatically.

MANDATORY RULES:
- Make ACTUAL code changes. Do NOT summarize, analyze, or propose.
- Each fix = 1 git commit with descriptive message.
- After each fix, run the verification command shown.
- Do NOT modify any application logic, routes, or vulnerability mechanics.

TASK 1: Fix identity mismatches (telemetry strings)
For each benchmark below, find and replace the OLD internal ID with the CORRECT 
registry ID in ALL files within that benchmark's folder:

  benchmarks/S7BEN-EASY-010/  → replace "S7BEN-HARD-015" with "S7BEN-EASY-010"
  benchmarks/S7BEN-EASY-011/  → replace "S7BEN-HARD-016" with "S7BEN-EASY-011"
  benchmarks/S7BEN-EASY-012/  → replace "S7BEN-HARD-017" with "S7BEN-EASY-012"
  benchmarks/S7BEN-EASY-014/  → replace "S7BEN-HARD-019" with "S7BEN-EASY-014"
  benchmarks/S7BEN-EASY-016/  → replace "S7BEN-VHARD-014" with "S7BEN-EASY-016"
  benchmarks/S7BEN-EASY-017/  → replace "S7BEN-VHARD-011" with "S7BEN-EASY-017"
  benchmarks/S7BEN-MED-018/   → replace "S7BEN-HARD-014" with "S7BEN-MED-018"
  benchmarks/S7BEN-MED-019/   → replace "S7BEN-VHARD-013" with "S7BEN-MED-019"

VERIFY: grep -r "S7BEN-HARD-015\|S7BEN-HARD-016\|S7BEN-HARD-017\|S7BEN-HARD-019\|S7BEN-VHARD-014\|S7BEN-VHARD-011\|S7BEN-HARD-014\|S7BEN-VHARD-013" benchmarks/S7BEN-EASY-* benchmarks/S7BEN-MED-018 benchmarks/S7BEN-MED-019
# Should return ZERO results

COMMIT: git commit -am "fix: resolve 8 identity mismatches — update telemetry strings to match registry IDs"

TASK 2: Fix HARD-001 nginx port
File: benchmarks/S7BEN-HARD-001/docker-compose.yml
Change the port mapping from "5050:8080" to "5050:80" (nginx listens on 80)
OR change nginx.conf to "listen 8080;"
VERIFY: grep -n "5050\|8080\|listen" benchmarks/S7BEN-HARD-001/docker-compose.yml benchmarks/S7BEN-HARD-001/*/nginx.conf
COMMIT: git commit -am "fix: HARD-001 nginx port mapping (5050:80)"

TASK 3: Fix VHARD-003 local port
File: benchmarks/S7BEN-VHARD-003/docker-compose.yml
Change port from 5072 to 389 (matching VPS LDAP configuration)
VERIFY: grep "389\|5072" benchmarks/S7BEN-VHARD-003/docker-compose.yml
COMMIT: git commit -am "fix: VHARD-003 port 389 (LDAP standard, matching VPS)"

TASK 4: Add CVE-010 to benchmarks.json
File: dashboard/data/benchmarks.json
Add entry for S7BEN-CVE-010 following the existing CVE entry format.
Check the benchmark's benchmark-config.json for the correct metadata.
VERIFY: grep "CVE-010" dashboard/data/benchmarks.json
COMMIT: git commit -am "fix: add S7BEN-CVE-010 (TeamCity) to API registry"

TASK 5: Scrub VHARD-009 hint contamination
In benchmarks/S7BEN-VHARD-009/:
- Remove any references to "Jinja2", "Twig", "Nunjucks" from UI templates
- Replace with generic terms like "template engine" or "rendering service"
- Check health endpoint responses for engine names
VERIFY: grep -ri "jinja\|twig\|nunjucks" benchmarks/S7BEN-VHARD-009/
COMMIT: git commit -am "fix: scrub template engine names from VHARD-009 UI"

TASK 6: Push all changes
git push origin main

FINAL VERIFICATION:
git log --oneline -10
# Should show 5-6 clean commits
```

---

## 9. WHAT NOT TO DO (Lessons from Sprint 10)

1. **DON'T rename folders without updating source code** — this is exactly what created the identity mismatch problem
2. **DON'T reuse retired benchmark numbers** — EASY-014 is retired, next EASY is EASY-022
3. **DON'T manually edit VPS files** — always commit locally and let CI/CD deploy (the VHARD-003 port 389 issue happened because someone edited VPS directly)
4. **DON'T move benchmarks without the full checklist** — Section 3.2 exists for a reason
5. **DON'T leave the remaining 12 MED benchmarks unaudited** — run Prompt 2 again targeting those specifically
