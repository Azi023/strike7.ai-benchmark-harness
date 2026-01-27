/**
 * SBEN-GQL-01: GraphQL API with SQL Injection Vulnerabilities
 *
 * INTENTIONALLY VULNERABLE CODE - DO NOT USE IN PRODUCTION
 *
 * This Apollo Server demonstrates:
 * 1. Enabled introspection in production (information disclosure)
 * 2. SQL injection in GraphQL resolvers (critical vulnerability)
 * 3. Insufficient input validation
 * 4. No query complexity/depth limiting
 */

const { ApolloServer } = require('@apollo/server');
const { expressMiddleware } = require('@apollo/server/express4');
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');

// Database connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://gqluser:GraphQLPass123!@postgres-db:5432/gqldb',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Load GraphQL schema
const typeDefs = fs.readFileSync(path.join(__dirname, 'schema.graphql'), 'utf8');

// Resolvers with INTENTIONAL SQL INJECTION vulnerabilities
const resolvers = {
  Query: {
    // Safe query - uses parameterized query
    users: async () => {
      const result = await pool.query('SELECT * FROM users ORDER BY id');
      return result.rows.map(row => ({
        id: row.id,
        username: row.username,
        email: row.email,
        role: row.role,
        createdAt: row.created_at
      }));
    },

    // CRITICAL VULNERABILITY: SQL Injection in searchUser
    // User input is directly concatenated into SQL query
    searchUser: async (_, { username }) => {
      console.log(`[VULNERABLE] Searching for user: ${username}`);

      // UNSAFE: Direct string concatenation - SQL INJECTION VULNERABILITY
      const query = `SELECT * FROM users WHERE username LIKE '%${username}%'`;

      console.log(`[VULNERABLE] Executing SQL: ${query}`);

      try {
        const result = await pool.query(query);
        return result.rows.map(row => ({
          id: row.id,
          username: row.username,
          email: row.email,
          role: row.role,
          createdAt: row.created_at
        }));
      } catch (error) {
        // Leaking SQL errors helps attackers understand the injection
        console.error('[ERROR] SQL Query failed:', error.message);
        throw new Error(`Database error: ${error.message}`);
      }
    },

    // Safe query with parameterization
    user: async (_, { id }) => {
      const result = await pool.query(
        'SELECT * FROM users WHERE id = $1',
        [id]
      );

      if (result.rows.length === 0) return null;

      const row = result.rows[0];
      return {
        id: row.id,
        username: row.username,
        email: row.email,
        role: row.role,
        createdAt: row.created_at
      };
    },

    // Returns admin data (should be protected but isn't)
    admins: async () => {
      const result = await pool.query('SELECT * FROM admins ORDER BY id');
      return result.rows.map(row => ({
        id: row.id,
        username: row.username,
        isSuperAdmin: row.is_super_admin,
        createdAt: row.created_at
      }));
    },

    // CRITICAL VULNERABILITY: SQL Injection in getSecret
    getSecret: async (_, { flagKey }) => {
      console.log(`[VULNERABLE] Getting secret: ${flagKey}`);

      // UNSAFE: Direct string concatenation
      const query = `SELECT * FROM secrets WHERE flag_key = '${flagKey}'`;

      console.log(`[VULNERABLE] Executing SQL: ${query}`);

      try {
        const result = await pool.query(query);

        if (result.rows.length === 0) return null;

        const row = result.rows[0];
        return {
          id: row.id,
          flagKey: row.flag_key,
          flagValue: row.flag_value,
          description: row.description,
          createdAt: row.created_at
        };
      } catch (error) {
        console.error('[ERROR] SQL Query failed:', error.message);
        throw new Error(`Database error: ${error.message}`);
      }
    },

    // Returns all secrets (no authentication!)
    allSecrets: async () => {
      const result = await pool.query('SELECT * FROM secrets ORDER BY id');
      return result.rows.map(row => ({
        id: row.id,
        flagKey: row.flag_key,
        flagValue: row.flag_value,
        description: row.description,
        createdAt: row.created_at
      }));
    },
  },

  Mutation: {
    // Safe mutation
    createUser: async (_, { username, email, role = 'user' }) => {
      const result = await pool.query(
        'INSERT INTO users (username, email, role) VALUES ($1, $2, $3) RETURNING *',
        [username, email, role]
      );

      const row = result.rows[0];
      return {
        id: row.id,
        username: row.username,
        email: row.email,
        role: row.role,
        createdAt: row.created_at
      };
    },

    // CRITICAL VULNERABILITY: SQL Injection in deleteUser
    deleteUser: async (_, { username }) => {
      console.log(`[VULNERABLE] Deleting user: ${username}`);

      // UNSAFE: Direct string concatenation
      const query = `DELETE FROM users WHERE username = '${username}'`;

      console.log(`[VULNERABLE] Executing SQL: ${query}`);

      try {
        const result = await pool.query(query);
        return result.rowCount > 0;
      } catch (error) {
        console.error('[ERROR] SQL Query failed:', error.message);
        throw new Error(`Database error: ${error.message}`);
      }
    },
  },
};

async function startServer() {
  const app = express();

  // Create Apollo Server with INSECURE configuration
  const server = new ApolloServer({
    typeDefs,
    resolvers,
    // VULNERABILITY: Introspection enabled in production
    introspection: true,
    // VULNERABILITY: Playground enabled in production
    // Note: Apollo Server 4 uses Apollo Sandbox instead
    // VULNERABILITY: No query complexity/depth limiting
    // VULNERABILITY: No rate limiting
  });

  await server.start();

  app.use(
    '/graphql',
    cors(),
    bodyParser.json(),
    expressMiddleware(server, {
      context: async ({ req }) => ({
        // No authentication/authorization implemented
        user: null,
      }),
    })
  );

  // Health check endpoint
  app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'graphql-api' });
  });

  // Root endpoint with documentation
  app.get('/', (req, res) => {
    res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>SBEN-GQL-01: GraphQL API</title>
        <style>
          body {
            font-family: 'Courier New', monospace;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background: #1e1e1e;
            color: #00ff00;
          }
          h1 { color: #ff6b6b; }
          h2 { color: #4ecdc4; }
          code {
            background: #2d2d2d;
            padding: 2px 6px;
            border-radius: 3px;
            color: #ffa500;
          }
          pre {
            background: #2d2d2d;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
          }
          .warning {
            background: #ff6b6b;
            color: white;
            padding: 10px;
            border-radius: 5px;
            margin: 20px 0;
          }
        </style>
      </head>
      <body>
        <h1>🔓 SBEN-GQL-01: GraphQL Introspection to SQL Injection</h1>

        <div class="warning">
          <strong>⚠️ WARNING:</strong> This API contains intentional security vulnerabilities.
          DO NOT expose to untrusted networks.
        </div>

        <h2>GraphQL Endpoint</h2>
        <p><code>POST /graphql</code> - Main GraphQL endpoint with introspection enabled</p>

        <h2>Example Introspection Query</h2>
        <pre>
query IntrospectionQuery {
  __schema {
    types {
      name
      fields {
        name
        type {
          name
        }
      }
    }
  }
}</pre>

        <h2>Example Search Query (Vulnerable)</h2>
        <pre>
query SearchUser {
  searchUser(username: "alice") {
    id
    username
    email
    role
  }
}</pre>

        <h2>Vulnerabilities</h2>
        <ul>
          <li><strong>CUSTOM-GQL-01:</strong> Introspection enabled in production</li>
          <li><strong>CWE-89:</strong> SQL injection in <code>searchUser</code> resolver</li>
          <li><strong>CUSTOM-GQL-02:</strong> No query complexity limiting</li>
        </ul>

        <h2>Access GraphQL Playground</h2>
        <p>Visit <a href="/graphql" style="color: #4ecdc4;">/graphql</a> to use Apollo Sandbox</p>

        <p style="text-align: center; margin-top: 50px; color: #888;">
          Strike7 Security Benchmarks - Phase 4
        </p>
      </body>
      </html>
    `);
  });

  const PORT = process.env.PORT || 4000;

  app.listen(PORT, () => {
    console.log(`🚀 GraphQL API running at http://localhost:${PORT}/graphql`);
    console.log(`⚠️  Introspection: ENABLED (VULNERABLE)`);
    console.log(`⚠️  SQL Injection: searchUser, getSecret, deleteUser (VULNERABLE)`);
    console.log(`📍 Health check: http://localhost:${PORT}/health`);
  });
}

// Handle errors
pool.on('error', (err) => {
  console.error('Unexpected database error:', err);
});

// Start server
startServer().catch(err => {
  console.error('Failed to start server:', err);
  process.exit(1);
});
