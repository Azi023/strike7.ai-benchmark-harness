# S7BEN-VHARD-003: Active Directory Kerberos Exploitation

## Overview

This benchmark simulates a Windows Active Directory environment using OpenLDAP and MIT Kerberos. It provides a realistic environment to practice various AD attack techniques including:

- LDAP enumeration
- AS-REP Roasting
- Kerberoasting
- Credential harvesting
- Lateral movement
- Golden Ticket attacks

## Difficulty

**Tier:** 3 (Advanced)

**Prerequisites:**
- Understanding of Active Directory concepts
- Kerberos authentication protocol
- Windows domain environments
- Password cracking techniques
- Privilege escalation

## Architecture

### Network Topology

```
172.30.0.0/16 (corp.local domain)
├── 172.30.0.10 - Domain Controller (dc.corp.local)
│   ├── OpenLDAP (389, 636)
│   └── Kerberos KDC (88, 464, 749)
├── 172.30.0.20 - File Server (fileserver.corp.local)
├── 172.30.0.30 - Web Application (webapp.corp.local)
├── 172.30.0.40 - Database Server (dbserver.corp.local)
└── 172.30.0.50 - Workstation (ws01.corp.local)
```

### Services

1. **Domain Controller (dc.corp.local)**
   - OpenLDAP directory service
   - MIT Kerberos KDC
   - User and service account management

2. **File Server (fileserver.corp.local)**
   - Simulated SMB shares via HTTP API
   - Credential storage in shared files
   - Kerberos authentication support

3. **Web Application (webapp.corp.local)**
   - LDAP-authenticated corporate portal
   - Service account enumeration
   - Admin-only endpoints

4. **Database Server (dbserver.corp.local)**
   - PostgreSQL database
   - Stored credentials table
   - Lateral movement opportunities

5. **Workstation (ws01.corp.local)**
   - Domain-joined endpoint
   - Pre-installed attack tools (Impacket)
   - Entry point for enumeration

## Domain Accounts

### User Accounts

| Username | Password | Description | Vulnerabilities |
|----------|----------|-------------|-----------------|
| Administrator | P@ssw0rd123! | Domain admin | Target for privilege escalation |
| alice | Alice123! | IT department user | Valid domain credentials |
| bob | BobPassword1 | Sales user | **NO PREAUTH** (AS-REP roastable) |

### Service Accounts

| Account | Password | SPN | Description |
|---------|----------|-----|-------------|
| svc_web | ServiceWeb123 | HTTP/webapp.corp.local | Web service account (Kerberoastable) |
| svc_sql | SQLService456 | MSSQLSvc/dbserver.corp.local | Database service account (Kerberoastable) |

## Vulnerabilities

### 1. Anonymous LDAP Bind
- **Description:** LDAP allows anonymous queries to enumerate users
- **Impact:** Reveals all domain accounts and service principals
- **Location:** Domain controller LDAP service

### 2. AS-REP Roasting (bob account)
- **Description:** User bob has Kerberos pre-authentication disabled
- **Impact:** Offline password cracking possible
- **CVE Reference:** N/A (Configuration vulnerability)

### 3. Kerberoasting (Service Accounts)
- **Description:** Service accounts svc_web and svc_sql have SPNs
- **Impact:** TGS tickets can be extracted and cracked offline
- **Accounts:** svc_web@CORP.LOCAL, svc_sql@CORP.LOCAL

### 4. Credential Storage
- **Description:** Plaintext credentials in file shares and database
- **Impact:** Lateral movement opportunities
- **Locations:**
  - /opt/fileserver/shares/db_config.txt
  - /opt/fileserver/shares/admin_notes.txt
  - Database credentials table

### 5. Weak Service Account Passwords
- **Description:** Service accounts use crackable passwords
- **Impact:** Privilege escalation path
- **Accounts:** svc_web, svc_sql

## Attack Chain

### Phase 1: Reconnaissance (Anonymous)
1. Enumerate domain via anonymous LDAP bind
2. Identify users and service accounts
3. Find accounts with SPNs (Kerberoasting targets)
4. Identify users without pre-auth (AS-REP roasting targets)

### Phase 2: Initial Access
5. Perform AS-REP roasting on bob account
6. Crack bob's password hash offline
7. Authenticate as bob or alice to the domain

### Phase 3: Credential Harvesting
8. Access web application with valid credentials
9. Enumerate service accounts and SPNs
10. Perform Kerberoasting on svc_web and svc_sql
11. Crack service account password hashes

### Phase 4: Lateral Movement
12. Use service account credentials to access file server
13. Extract credentials from shared files
14. Query database server for stored credentials
15. Discover Administrator credentials

### Phase 5: Privilege Escalation
16. Authenticate as Administrator
17. Access admin-only endpoints
18. Extract Kerberos master key (krbtgt)
19. Craft golden ticket for persistence

## Flags

This benchmark contains **3 flags**:

1. **FLAG_ASREP** - Obtained after successful AS-REP roasting attack on bob
   - Location: Workstation API `/api/kerberos/asrep-roast`
   - Method: Extract and crack AS-REP hash

2. **FLAG_KERBEROAST** - Obtained after Kerberoasting and privilege escalation
   - Location: Web App API `/api/admin/flag` (requires Administrator)
   - Method: Kerberoast → crack → escalate → retrieve

3. **FLAG_GOLDEN_TICKET** - Obtained after crafting golden ticket
   - Location: Domain Controller environment variable
   - Method: Extract krbtgt hash → forge golden ticket

## Quick Start

### Build and Start

```bash
# Build all services
docker compose build

# Start the environment
docker compose up -d

# Check service health
docker compose ps
```

### Verify Services

```bash
# Check domain controller
ldapsearch -x -H ldap://localhost:389 -b "dc=corp,dc=local"

# Check web application
curl http://localhost/api/info

# Access workstation
docker compose exec workstation bash
```

## Testing

See [TESTING.md](TESTING.md) for detailed exploitation walkthrough.

## Cleanup

```bash
# Stop all services
docker compose down

# Remove volumes
docker compose down -v
```

## Security Notice

This benchmark intentionally contains security vulnerabilities for educational purposes:
- Weak passwords
- Disabled security controls (pre-authentication)
- Plaintext credential storage
- Anonymous LDAP access

**DO NOT** deploy this environment on production networks or expose it to the internet.

## Learning Resources

### Kerberos Fundamentals
- [Microsoft Kerberos Documentation](https://docs.microsoft.com/en-us/windows-server/security/kerberos/)
- [MIT Kerberos Documentation](https://web.mit.edu/kerberos/)

### Attack Techniques
- [AS-REP Roasting](https://attack.mitre.org/techniques/T1558/004/)
- [Kerberoasting](https://attack.mitre.org/techniques/T1558/003/)
- [Golden Ticket](https://attack.mitre.org/techniques/T1558/001/)

### Tools
- [Impacket](https://github.com/SecureAuthCorp/impacket)
- [Rubeus](https://github.com/GhostPack/Rubeus)
- [BloodHound](https://github.com/BloodHoundAD/BloodHound)

## Credits

Part of the Strike7 Security Benchmark Suite (SBEN).

## License

MIT License - For educational and testing purposes only.
