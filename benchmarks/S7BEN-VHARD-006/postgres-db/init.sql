-- SBEN-GQL-01: GraphQL Database Initialization
-- This schema supports GraphQL introspection and SQL injection testing

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
    ('admin', '$2b$10$abcdefghijklmnopqrstuvwxyz123456789', TRUE),
    ('moderator', '$2b$10$zyxwvutsrqponmlkjihgfedcba987654321', FALSE);

-- Insert flags into secrets table
INSERT INTO secrets (flag_key, flag_value, description) VALUES
    ('introspection', 'S7BEN{graphql_introspection_schema_exposed_a1b2c3}', 'Flag for discovering GraphQL schema via introspection'),
    ('sqli', 'S7BEN{graphql_resolver_sql_injection_d4e5f6}', 'Flag for exploiting SQL injection in GraphQL resolver'),
    ('admin_secret', 'S7BEN{admin_panel_access_via_graphql_g7h8i9}', 'Flag for accessing admin functionality');

-- Create indexes for better performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_admins_username ON admins(username);
CREATE INDEX idx_secrets_flag_key ON secrets(flag_key);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO gqluser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO gqluser;
