# S7BEN-VHARD-006: GraphQL Introspection to SQL Injection

## Overview

This benchmark demonstrates security vulnerabilities in GraphQL APIs, specifically focusing on enabled introspection and SQL injection in GraphQL resolvers. It showcases how attackers can discover schema information and exploit unsafe database queries through GraphQL endpoints.

## Difficulty

**Tier:** 2 (Intermediate)

**Prerequisites:**
- Understanding of GraphQL query language and schema
- Knowledge of GraphQL introspection mechanism
- Familiarity with SQL injection techniques
- Experience with REST/GraphQL APIs
- Basic understanding of PostgreSQL

## Architecture

```
┌─────────────────────────────────────┐
│  graphql-api (Apollo Server)        │
│  - GraphQL endpoint at /graphql     │
│  - Introspection ENABLED            │
│  - Vulnerable SQL queries           │
│  Port: 4000 (exposed)               │
│  IP: 172.24.0.10                    │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│  postgres-db (PostgreSQL 15)        │
│  - Users table                      │
│  - Admins table                     │
│  - Secrets table (flags)            │
│  Port: 5432 (internal)              │
│  IP: 172.24.0.20                    │
└─────────────────────────────────────┘
```

## Vulnerabilities

1. **GraphQL Introspection Enabled (CUSTOM-GQL-01)**
   - Introspection queries expose full schema
   - Attackers can enumerate all types, fields, and queries
   - Severity: Medium

2. **SQL Injection in searchUser Resolver (CWE-89)**
   - Direct string concatenation in SQL queries
   - No input validation or parameterization
   - Allows UNION-based SQLi for data extraction
   - Severity: Critical

3. **SQL Injection in getSecret Resolver (CWE-89)**
   - Vulnerable flag retrieval query
   - Enables direct access to secrets table
   - Severity: Critical

4. **Insufficient Access Controls (CUSTOM-GQL-02)**
   - allSecrets query returns all flags without authentication
   - No query depth or complexity limiting
   - Severity: Medium

## Attack Chain

1. **GraphQL Discovery** - Identify GraphQL endpoint and test introspection
2. **Schema Enumeration** - Extract complete schema via `__schema` queries
3. **SQL Injection Discovery** - Test searchUser with SQL syntax
4. **Data Extraction** - Use UNION SELECT to extract secrets
5. **Flag Retrieval** - Extract both flags from database

## Flags

- **FLAG 1:** `S7BEN{graphql_introspection_schema_exposed_a1b2c3}` - Located in `secrets` table (flag_key='introspection')
- **FLAG 2:** `S7BEN{graphql_resolver_sql_injection_d4e5f6}` - Located in `secrets` table (flag_key='sqli')

## Quick Start

```bash
# Build and start services
docker compose up -d

# Check service health
docker compose ps
make test

# Access GraphQL API
curl http://localhost:4000

# Access Apollo Sandbox
open http://localhost:4000/graphql
```

## Tools Required

- **curl** - For HTTP requests
- **GraphQL client** - Altair, GraphiQL, Insomnia, or Apollo Sandbox (built-in)
- **jq** - For JSON parsing (optional)
- **Python 3.x** - For automation (optional)

## Testing

See [TESTING.md](TESTING.md) for detailed exploitation guide with:
- GraphQL introspection queries
- Schema enumeration techniques
- SQL injection payloads
- UNION-based data extraction
- Flag retrieval methods

## Cleanup

```bash
# Stop all services
docker compose down

# Remove volumes
docker compose down -v
```

## Learning Resources

- [GraphQL Official Documentation](https://graphql.org/learn/)
- [GraphQL Introspection](https://graphql.org/learn/introspection/)
- [OWASP GraphQL Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html)
- [Exploiting GraphQL APIs](https://blog.yeswehack.com/yeswerhackers/how-exploit-graphql-endpoint-bug-bounty/)

## Security Notice

This benchmark contains intentional security vulnerabilities:
- GraphQL introspection enabled in production
- SQL injection in GraphQL resolvers
- No input validation or sanitization
- No authentication or authorization
- No query complexity/depth limiting

**DO NOT** expose this environment to untrusted networks.

## License

MIT License - For educational purposes only.
