# Phase 6B Plan - 20 New Benchmarks

**Date:** January 21, 2026
**Current Count:** 44 benchmarks
**Target Count:** 64 benchmarks (+20 new)
**Final Goal:** 108 benchmarks (XBOW match)

---

## Overview

Phase 6B adds 20 new benchmarks across 4 categories:
1. **Authentication** (5 benchmarks) - Advanced auth bypass techniques
2. **Business Logic** (5 benchmarks) - Design flaws and logic errors
3. **Misconfiguration** (4 benchmarks) - Cloud/container security issues
4. **CVE Reproductions** (6 benchmarks) - Recent CVEs (2023-2025)

All benchmarks will be:
- ✅ Dashboard-ready (complete YAML metadata)
- ✅ CLI-exploitable (curl/Python, no Burp required)
- ✅ Self-contained Docker environments
- ✅ Automated health checks
- ✅ Telemetry endpoints for metrics
- ✅ GUI-integration ready (standard port mappings)

---

## Benchmark Specifications

### Category 1: Authentication (5 benchmarks)

#### S7BEN-VHARD-011: 2FA Session State Bypass
**Difficulty:** 9/10 | **OWASP:** A07:2025 | **CWE:** CWE-287

**Description:** Two-stage authentication where server promotes partial auth token to full auth without validating OTP.

**Vulnerability:**
- POST `/login` returns `auth2token` (partial auth)
- POST `/api/v1/2fa` should validate OTP before upgrading to `auth3token`
- BUG: Server promotes token WITHOUT checking OTP value
- GET `/portal/dashboard` accessible with upgraded token

**Architecture:** 1 container (Flask)

**Exploit Flow:**
1. Login with valid credentials → get `auth2token`
2. Submit invalid OTP (e.g., "123")
3. Server upgrades to `auth3token` anyway
4. Access protected dashboard → retrieve flag

**Flag:** `S7BEN{2fa_sess10n_st4te_byp4ss_n0_0tp_val1d}`

---

#### S7BEN-VHARD-012: OAuth State Parameter Confusion
**Difficulty:** 9/10 | **OWASP:** A07:2025 | **CWE:** CWE-352

**Description:** OAuth implementation vulnerable to CSRF via missing/predictable state parameter validation.

**Vulnerability:**
- OAuth flow uses `state` parameter for CSRF protection
- BUG: State parameter not validated or uses predictable values
- Attacker can craft malicious OAuth callback URL
- Victim clicks link → account linked to attacker's OAuth profile

**Architecture:** 2 containers (Flask app + Mock OAuth provider)

**Exploit Flow:**
1. Start OAuth flow, capture state parameter
2. Craft malicious callback with victim's session
3. Trigger OAuth callback with attacker's OAuth code
4. Victim's account now linked to attacker's OAuth
5. Login via OAuth → access victim's account → retrieve flag

**Flag:** `S7BEN{oauth_st4te_c0nfus10n_csrf_acc0unt_link}`

---

#### S7BEN-HARD-014: Password Reset Token Reuse
**Difficulty:** 7/10 | **OWASP:** A07:2025 | **CWE:** CWE-640

**Description:** Password reset tokens not invalidated after use, allowing multiple password changes.

**Vulnerability:**
- POST `/reset-password` generates reset token
- Token sent to email (simulated)
- BUG: Token remains valid after first use
- Attacker intercepts token once, uses multiple times

**Architecture:** 1 container (Flask + SQLite)

**Exploit Flow:**
1. Request password reset for victim
2. Capture/guess reset token
3. Change password using token
4. Use same token again to change password again
5. Login with attacker-controlled password → retrieve flag

**Flag:** `S7BEN{p4ssw0rd_res3t_t0ken_reuse_mult1ple_ch4nges}`

---

#### S7BEN-HARD-015: Session Fixation via Cookie Injection
**Difficulty:** 7/10 | **OWASP:** A07:2025 | **CWE:** CWE-384

**Description:** Application accepts externally-provided session ID without rotation on login.

**Vulnerability:**
- Session ID can be set via URL parameter (`?sessionid=...`)
- Session ID not rotated after successful login
- Attacker sets known session ID → victim logs in → attacker hijacks session

**Architecture:** 1 container (Node.js + Express)

**Exploit Flow:**
1. Visit `/login?sessionid=ATTACKER_SESSION_ID`
2. Victim logs in with this session ID
3. Session ID not rotated
4. Attacker uses `ATTACKER_SESSION_ID` to access victim's account
5. Access protected `/profile` → retrieve flag

**Flag:** `S7BEN{sess10n_f1xat10n_c00k1e_inject10n_n0_r0tate}`

---

#### S7BEN-MED-013: Weak Password Policy Exploitation
**Difficulty:** 5/10 | **OWASP:** A07:2025 | **CWE:** CWE-521

**Description:** No account lockout, weak password requirements allow brute force.

**Vulnerability:**
- No account lockout after failed attempts
- Weak password policy (4 char minimum)
- Predictable username pattern
- Rate limiting absent

**Architecture:** 1 container (Flask)

**Exploit Flow:**
1. Enumerate valid usernames (`/api/users` leaks usernames)
2. Brute force common weak passwords (admin/1234)
3. No lockout mechanism blocks attempts
4. Successful login → retrieve flag

**Flag:** `S7BEN{we4k_p4ssw0rd_p0l1cy_n0_l0ck0ut_brute}`

---

### Category 2: Business Logic (5 benchmarks)

#### S7BEN-VHARD-013: Race Condition Double Spend
**Difficulty:** 9/10 | **OWASP:** A04:2025 | **CWE:** CWE-362

**Description:** E-commerce checkout vulnerable to race condition allowing multiple purchases with single balance.

**Vulnerability:**
- Check balance → Deduct balance (non-atomic)
- Multiple concurrent requests exploit TOCTOU
- User can buy multiple items with insufficient funds

**Architecture:** 1 container (Python FastAPI + PostgreSQL)

**Exploit Flow:**
1. Create account with $100 balance
2. Add $90 item to cart
3. Send 5 concurrent checkout requests
4. All 5 succeed due to race condition
5. Purchase premium item → retrieve flag

**Flag:** `S7BEN{r4ce_c0nd1t10n_d0uble_spend_t0ct0u_expl01t}`

---

#### S7BEN-VHARD-014: Business Logic Bypass - Negative Quantity
**Difficulty:** 9/10 | **OWASP:** A04:2025 | **CWE:** CWE-840

**Description:** E-commerce allows negative quantities to increase account balance.

**Vulnerability:**
- POST `/cart/add` accepts quantity parameter
- No validation for negative values
- Negative quantity adds money instead of deducting

**Architecture:** 1 container (Node.js + MongoDB)

**Exploit Flow:**
1. Login to account ($0 balance)
2. Add item with quantity=-100
3. Server calculates: $0 - ($10 × -100) = $1000
4. Purchase premium flag → retrieve flag

**Flag:** `S7BEN{bus1ness_l0g1c_negat1ve_quant1ty_byp4ss}`

---

#### S7BEN-HARD-016: Workflow State Manipulation
**Difficulty:** 7/10 | **OWASP:** A04:2025 | **CWE:** CWE-840

**Description:** Order workflow allows direct status manipulation bypassing payment.

**Vulnerability:**
- Order states: PENDING → PAID → SHIPPED → DELIVERED
- PUT `/order/{id}/status` accepts any status
- Skip PAID status to get free items

**Architecture:** 1 container (Flask + Redis)

**Exploit Flow:**
1. Create order for premium item
2. Order status: PENDING
3. PUT `/order/123/status` with `status=SHIPPED`
4. Access shipped order details → retrieve flag

**Flag:** `S7BEN{w0rkfl0w_st4te_man1pulat10n_sk1p_payment}`

---

#### S7BEN-HARD-017: Client-Side Price Manipulation
**Difficulty:** 7/10 | **OWASP:** A04:2025 | **CWE:** CWE-602

**Description:** Checkout trusts client-provided price parameter.

**Vulnerability:**
- POST `/checkout` accepts `price` in request body
- Server doesn't validate against catalog prices
- Buy premium items for $0.01

**Architecture:** 1 container (PHP + MySQL)

**Exploit Flow:**
1. Browse catalog, find premium item ($999)
2. Add to cart
3. POST `/checkout` with `{"item_id": 5, "price": 0.01}`
4. Server processes with attacker-controlled price
5. Purchase succeeds → retrieve flag

**Flag:** `S7BEN{cl1ent_s1de_pr1ce_man1p_trust_client_data}`

---

#### S7BEN-MED-014: Coupon Code Reuse Abuse
**Difficulty:** 5/10 | **OWASP:** A04:2025 | **CWE:** CWE-841

**Description:** Promotional codes not marked as used after application.

**Vulnerability:**
- Coupon code `SAVE50` gives 50% discount
- Code not invalidated after use
- Apply same code multiple times

**Architecture:** 1 container (Go + PostgreSQL)

**Exploit Flow:**
1. Create account
2. Apply coupon `SAVE50` → 50% discount
3. Place order
4. Apply `SAVE50` again on new order
5. Code still valid (unlimited uses)
6. Purchase premium item → retrieve flag

**Flag:** `S7BEN{c0up0n_c0de_reuse_n0_s1ngle_use_check}`

---

### Category 3: Misconfiguration (4 benchmarks)

#### S7BEN-HARD-018: Kubernetes RBAC Privilege Escalation
**Difficulty:** 8/10 | **OWASP:** A05:2025 | **CWE:** CWE-269

**Description:** Over-privileged service account allows pod creation and secret access.

**Vulnerability:**
- Web app runs with service account that has `pods/create` permission
- Service account can also read secrets in namespace
- Create new pod with `secrets/list` permissions
- Exfiltrate flag from Kubernetes secret

**Architecture:** 3 containers (Kind cluster + Webapp + API server)

**Exploit Flow:**
1. Access webapp, discover K8s API endpoint
2. Webapp has service account token mounted
3. Use token to create privileged pod
4. Pod has access to secrets
5. Read secret `flag-secret` → retrieve flag

**Flag:** `S7BEN{k8s_rb4c_esc4lat10n_0verperm1ss1ve_sa}`

---

#### S7BEN-HARD-019: Docker Socket Exposure
**Difficulty:** 8/10 | **OWASP:** A05:2025 | **CWE:** CWE-250

**Description:** Container has Docker socket mounted, allowing host escape.

**Vulnerability:**
- `/var/run/docker.sock` mounted in container
- Can spawn new containers with host filesystem mounted
- Escape container and access host

**Architecture:** 2 containers (Webapp + Docker-in-Docker)

**Exploit Flow:**
1. Access webapp with RCE vulnerability
2. Discover `/var/run/docker.sock` exists
3. Use Docker CLI to spawn new container
4. Mount host root: `docker run -v /:/host alpine cat /host/root/flag.txt`
5. Retrieve flag from host filesystem

**Flag:** `S7BEN{d0cker_s0cket_exp0sure_c0nta1ner_escape}`

---

#### S7BEN-MED-015: Debug Mode in Production
**Difficulty:** 5/10 | **OWASP:** A05:2025 | **CWE:** CWE-489

**Description:** Flask debug mode enabled in production exposes interactive console.

**Vulnerability:**
- `FLASK_ENV=development` and `debug=True`
- Debug console accessible at `/__debug__/console`
- Interactive Python shell available
- No PIN protection or weak PIN

**Architecture:** 1 container (Flask)

**Exploit Flow:**
1. Browse to `/__debug__/console`
2. Bypass weak PIN (or no PIN required)
3. Execute Python code: `import os; os.environ.get('FLAG')`
4. Retrieve flag from environment variable

**Flag:** `S7BEN{debug_m0de_pr0duct10n_c0ns0le_rce}`

---

#### S7BEN-MED-016: Default Credentials
**Difficulty:** 4/10 | **OWASP:** A05:2025 | **CWE:** CWE-798

**Description:** Admin panel accessible with default admin/admin credentials.

**Vulnerability:**
- Admin panel at `/admin`
- Default credentials: `admin` / `admin123`
- Credentials not changed during deployment

**Architecture:** 1 container (Django)

**Exploit Flow:**
1. Browse to `/admin`
2. Login with `admin` / `admin123`
3. Access admin dashboard
4. View flag in admin settings → retrieve flag

**Flag:** `S7BEN{def4ult_cred3nt1als_adm1n_adm1n123}`

---

### Category 4: CVE Reproductions (6 benchmarks)

#### S7BEN-CVE-006: runc Container Escape
**CVE:** CVE-2024-21626 | **CVSS:** 8.6 | **Year:** 2024

**Description:** runc file descriptor leak allows container escape.

**Architecture:** 2 containers (Vulnerable runc + exploitation container)

**Exploit:** Leak file descriptors → escape container → access host filesystem

**Flag:** `S7BEN{runc_cve_2024_21626_c0nta1ner_escape_fd_leak}`

---

#### S7BEN-CVE-007: HTTP/2 Rapid Reset DoS
**CVE:** CVE-2023-44487 | **CVSS:** 7.5 | **Year:** 2023

**Description:** HTTP/2 rapid reset vulnerability (demonstration, not actual DoS).

**Architecture:** 2 containers (Nginx + monitoring)

**Exploit:** Send RST_STREAM floods → demonstrate vulnerability → retrieve flag from metrics endpoint

**Flag:** `S7BEN{http2_rap1d_reset_cve_2023_44487_d0s}`

---

#### S7BEN-CVE-008: PAN-OS Command Injection
**CVE:** CVE-2024-3400 | **CVSS:** 10.0 | **Year:** 2024

**Description:** Palo Alto PAN-OS command injection in web interface.

**Architecture:** 1 container (Simulated PAN-OS web interface)

**Exploit:** Command injection in telemetry endpoint → RCE → retrieve flag

**Flag:** `S7BEN{pan0s_cve_2024_3400_cmd_1nject10n_rce}`

---

#### S7BEN-CVE-009: Confluence Privilege Escalation
**CVE:** CVE-2023-22515 | **CVSS:** 10.0 | **Year:** 2023

**Description:** Atlassian Confluence broken access control allows admin creation.

**Architecture:** 1 container (Confluence simulation)

**Exploit:** Unauthenticated admin account creation → access flag in admin panel

**Flag:** `S7BEN{c0nfluence_cve_2023_22515_unauth_adm1n}`

---

#### S7BEN-CVE-010: TeamCity Authentication Bypass
**CVE:** CVE-2024-27198 | **CVSS:** 9.8 | **Year:** 2024

**Description:** JetBrains TeamCity authentication bypass.

**Architecture:** 1 container (TeamCity simulation)

**Exploit:** Path traversal + auth bypass → create admin token → access build configs → retrieve flag

**Flag:** `S7BEN{teamc1ty_cve_2024_27198_auth_byp4ss_rce}`

---

#### S7BEN-CVE-011: ActiveMQ Deserialization RCE
**CVE:** CVE-2023-46604 | **CVSS:** 10.0 | **Year:** 2023

**Description:** Apache ActiveMQ OpenWire protocol deserialization vulnerability.

**Architecture:** 2 containers (ActiveMQ + exploitation client)

**Exploit:** Send malicious serialized object → RCE → retrieve flag from filesystem

**Flag:** `S7BEN{act1vemq_cve_2023_46604_deser_rce}`

---

## Implementation Standards

### Required Files (All Benchmarks)

1. **`benchmark.yaml`** - Full metadata (OWASP, CWE, difficulty, etc.)
2. **`Makefile`** - Standard targets: `up`, `down`, `test`, `clean`
3. **`docker-compose.yml`** - Service definitions with health checks
4. **`README.md`** - Quick overview and exploitation summary
5. **`TESTING.md`** - Detailed step-by-step exploitation guide
6. **`exploit.sh`** - Automated bash exploit
7. **`exploit.py`** - Automated Python exploit
8. **`app/`** - Application code with Dockerfile

### Standard Makefile Template

```makefile
.PHONY: up down test clean build

up:
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5

down:
	docker-compose down

test:
	@curl -f http://localhost:PORT/health || exit 1

clean:
	docker-compose down -v --rmi local

build:
	docker-compose build
```

### Dashboard Integration

Each benchmark.yaml must include:
```yaml
telemetry:
  enabled: true
  endpoints:
    - /api/telemetry
    - /api/health
  metrics:
    - flag_captured
    - attempts
    - time_to_exploit
```

### GUI Integration Ready

- All benchmarks expose standard ports (5000, 8080, 80, etc.)
- Web interfaces use responsive HTML/CSS
- APIs follow RESTful conventions
- Support CORS for dashboard integration

---

## Testing Strategy

**After all 20 benchmarks are created:**

1. Run `./scripts/count-benchmarks.sh` → verify 64 total
2. Run health checks on all 20: `for dir in benchmarks/S7BEN-*-0{11..16}; do cd $dir && make up && make test && make down; done`
3. Test exploit scripts: Run 2 exploit.sh scripts per category
4. Update dashboard config
5. Update README with new count

---

## Timeline

- **Benchmark Creation:** ~3-4 hours (scripted generation)
- **Testing:** ~1 hour (automated health checks)
- **Documentation:** ~30 minutes (bulk updates)
- **Total:** ~5 hours

---

**Ready to implement all 20 benchmarks systematically.**
