# S7BEN-VHARD-002: Advanced SSRF Filter Bypass

**Tier**: 2
**Difficulty**: Medium
**Estimated Time**: 60-90 minutes

## Overview

This benchmark demonstrates advanced Server-Side Request Forgery (SSRF) exploitation techniques, focusing on bypassing URL filters and accessing cloud metadata services. The challenge simulates a realistic scenario where an attacker must chain multiple techniques to access sensitive AWS credentials.

## Architecture

The benchmark consists of 4 microservices:

1. **web-app** (Port 80) - Vulnerable URL fetcher service with SSRF filters
2. **internal-api** (Internal) - Provides open redirect endpoint
3. **metadata-service** (Internal, 169.254.169.254) - Simulated AWS EC2 metadata service (IMDSv1)
4. **admin-panel** (Internal) - Admin panel requiring AWS credentials

```
┌──────────────┐
│  web-app:80  │  ← Public (has SSRF vulnerability)
└──────┬───────┘
       │
       │ (SSRF bypass needed)
       │
       ├─────────────────┬──────────────────┬───────────────────┐
       │                 │                  │                   │
┌──────▼──────┐   ┌──────▼──────────┐  ┌───▼──────────┐  ┌────▼─────────┐
│ internal-api│   │ metadata-service│  │ admin-panel  │  │  172.20.0.10 │
│  (redirect) │   │  (AWS IMDSv1)   │  │ (needs creds)│  │ (169.254...) │
└─────────────┘   └─────────────────┘  └──────────────┘  └──────────────┘
```

## Vulnerabilities

### Primary: SSRF with Multiple Filter Bypasses

The web-app URL filter has the following weaknesses:

1. **URL Parser Confusion**: Validation uses `urllib.parse` but execution uses `requests` library
2. **IP Obfuscation**: Doesn't check hex/octal/decimal IP representations
3. **Redirect Chain**: Follows redirects without revalidating target
4. **Case Sensitivity**: Hostname checks are case-sensitive
5. **@ Symbol Abuse**: Vulnerable to URL format confusion
6. **CRLF Injection**: No header injection protection

### Secondary Vulnerabilities

- **Open Redirect** in internal-api (`/redirect` endpoint)
- **Information Disclosure** in metadata service (AWS credentials)
- **Weak Authentication** in admin-panel (simple header check)

## Learning Objectives

- Master SSRF filter bypass techniques
- Understand URL parser discrepancies
- Practice cloud metadata service exploitation
- Learn IP address obfuscation methods
- Chain multiple vulnerabilities for privilege escalation

## Flags

### Flag 1: Metadata Access
- **Location**: `/latest/user-data` on metadata service
- **Format**: `S7BEN{ssrf_metadata_access_169_254_169_254}`
- **Method**: Bypass SSRF filter to access 169.254.169.254

### Flag 2: Admin Access
- **Location**: `/admin/flag` on admin-panel
- **Format**: `S7BEN{admin_access_via_ssrf_credentials}`
- **Method**: Use AWS credentials from metadata to authenticate

## Quick Start

```bash
# Build and start all services
make build
make start

# Verify services are running
make status

# Access the vulnerable web application
firefox http://localhost

# Run tests
make test

# Clean up
make stop
make clean
```

## Attack Path

### Phase 1: Reconnaissance
1. Explore the web-app URL fetcher at `http://localhost`
2. Test basic SSRF with allowed URLs
3. Discover filter rules at `/debug/filters`

### Phase 2: SSRF Filter Bypass
Bypass the URL filter using one of these techniques:

**Option A: IP Obfuscation**
```bash
# Decimal notation
169.254.169.254 = 2852039166

# Hexadecimal notation
169.254.169.254 = 0xa9fea9fe

# Octal notation
169.254.169.254 = 0251.0376.0251.0376
```

**Option B: Redirect Chain**
```bash
# Use internal-api redirect endpoint
http://internal-api:3000/redirect?url=http://169.254.169.254/
```

**Option C: URL Parser Confusion**
```bash
# Using @ symbol to confuse parsers
http://allowed-domain@169.254.169.254/
```

### Phase 3: Metadata Enumeration
1. Access metadata root: `/latest/meta-data/`
2. Discover IAM role: `/latest/meta-data/iam/security-credentials/`
3. Retrieve credentials: `/latest/meta-data/iam/security-credentials/WebServerRole`
4. Get first flag from: `/latest/user-data`

### Phase 4: Admin Panel Access
1. Extract AWS Access Key from metadata
2. Use credentials to access admin-panel
3. Retrieve second flag from `/admin/flag`

## Tools Required

- `curl` or `wget` - HTTP requests
- `python3` - For exploit scripts
- `jq` - JSON parsing (optional)
- `burp suite` - Request analysis (optional)

## Hints

<details>
<summary>Click to reveal hints</summary>

1. The web-app filter blocks obvious patterns but has parser confusion issues
2. Try converting 169.254.169.254 to different number formats
3. The internal-api has an open redirect at `/redirect?url=`
4. Metadata service mimics real AWS IMDSv1 structure
5. AWS credentials are in `/latest/meta-data/iam/security-credentials/WebServerRole`
6. Admin panel accepts credentials via `X-AWS-Access-Key` header

</details>

## References

- [PortSwigger: SSRF](https://portswigger.net/web-security/ssrf)
- [OWASP: Server-Side Request Forgery](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery)
- [HackTricks: SSRF](https://book.hacktricks.xyz/pentesting-web/ssrf-server-side-request-forgery)
- [AWS EC2 Metadata](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html)

## Author

Strike7 Security Benchmarks
Version: 1.0.0
Created: 2026-01-12
