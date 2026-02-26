#!/bin/sh
# SBEN-GQL-01: GraphQL Database Initialization with Dynamic Flags
# This script generates unique flags on every fresh container start

set -e

# Generate dynamic flag suffixes
SUFFIX_INTROSPECTION=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)
SUFFIX_SQLI=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)
SUFFIX_ADMIN=$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)

FLAG_INTROSPECTION="S7BEN{graphql_introspection_schema_exposed_${SUFFIX_INTROSPECTION}}"
FLAG_SQLI="S7BEN{graphql_resolver_sql_injection_${SUFFIX_SQLI}}"
FLAG_ADMIN="S7BEN{admin_panel_access_via_graphql_${SUFFIX_ADMIN}}"

echo "[init.sh] Generating dynamic flags for database seeding"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Users table with sample data
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) NOT NULL,
        role VARCHAR(20) DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Admins table with privileged accounts
    CREATE TABLE admins (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        is_super_admin BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Secrets table containing flags
    CREATE TABLE secrets (
        id SERIAL PRIMARY KEY,
        flag_key VARCHAR(50) UNIQUE NOT NULL,
        flag_value TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Insert sample users
    INSERT INTO users (username, email, role) VALUES
        ('alice', 'alice@example.com', 'user'),
        ('bob', 'bob@example.com', 'user'),
        ('charlie', 'charlie@example.com', 'moderator'),
        ('david', 'david@example.com', 'user'),
        ('eve', 'eve@example.com', 'user');

    -- Insert admin accounts
    INSERT INTO admins (username, password_hash, is_super_admin) VALUES
        ('admin', '\$2b\$10\$abcdefghijklmnopqrstuvwxyz123456789', TRUE),
        ('moderator', '\$2b\$10\$zyxwvutsrqponmlkjihgfedcba987654321', FALSE);

    -- Insert dynamically generated flags into secrets table
    INSERT INTO secrets (flag_key, flag_value, description) VALUES
        ('introspection', '${FLAG_INTROSPECTION}', 'Flag for discovering GraphQL schema via introspection'),
        ('sqli', '${FLAG_SQLI}', 'Flag for exploiting SQL injection in GraphQL resolver'),
        ('admin_secret', '${FLAG_ADMIN}', 'Flag for accessing admin functionality');

    -- Create indexes for better performance
    CREATE INDEX idx_users_username ON users(username);
    CREATE INDEX idx_users_role ON users(role);
    CREATE INDEX idx_admins_username ON admins(username);
    CREATE INDEX idx_secrets_flag_key ON secrets(flag_key);

    -- Grant permissions
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO gqluser;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO gqluser;
EOSQL

# Write flags to shared volume for scoring/validation
cat > /flags/flags.txt <<EOF2
FLAG_INTROSPECTION=${FLAG_INTROSPECTION}
FLAG_SQLI=${FLAG_SQLI}
FLAG_ADMIN=${FLAG_ADMIN}
EOF2
chmod 644 /flags/flags.txt

echo "[init.sh] Database initialized with dynamic flags"
