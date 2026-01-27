-- SBEN-CHAIN-01 Database Initialization
-- PostgreSQL 15

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create secrets table (STEP 5: Contains the flag)
CREATE TABLE IF NOT EXISTS secrets (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    requires_chain_proof BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create application data table
CREATE TABLE IF NOT EXISTS app_data (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample users
INSERT INTO users (username, email, role) VALUES
    ('user', 'user@example.com', 'user'),
    ('admin', 'admin@example.com', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Insert flag into secrets table
-- STEP 5: Flag accessible via database credentials extracted from worker
-- The actual flag value will be generated dynamically by the application
INSERT INTO secrets (key, value, description, requires_chain_proof) VALUES
    ('exploitation_flag', 'SBEN{microservices_chain_PLACEHOLDER}', 'Exploitation proof flag - requires complete chain', TRUE),
    ('database_password', 'SecureDBPass12345!', 'Database password', FALSE)
ON CONFLICT (key) DO NOTHING;

-- Insert sample application data
INSERT INTO app_data (key, value) VALUES
    ('config', '{"version": "1.0.0", "environment": "production"}'),
    ('stats', '{"users": 2, "requests": 0}')
ON CONFLICT (key) DO NOTHING;

-- Create worker user with limited permissions
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'workeruser') THEN
        CREATE USER workeruser WITH PASSWORD 'SecureDBPass12345!';
    END IF;
END
$$;

-- Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO workeruser;
GRANT SELECT ON secrets TO workeruser;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_secrets_key ON secrets(key);
CREATE INDEX IF NOT EXISTS idx_app_data_key ON app_data(key);

-- Add comments
COMMENT ON TABLE secrets IS 'Contains sensitive data including the exploitation flag (Step 5)';
COMMENT ON COLUMN secrets.requires_chain_proof IS 'Flag that requires complete attack chain to retrieve';

-- Display initialization complete
SELECT 'Database initialized successfully' AS status,
       COUNT(*) AS users_count FROM users;

SELECT 'Secrets table ready' AS status,
       COUNT(*) AS secrets_count FROM secrets;
