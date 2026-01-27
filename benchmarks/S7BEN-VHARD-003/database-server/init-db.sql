-- Initialize corporate database
CREATE DATABASE corpdb;

\c corpdb;

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100),
    department VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Credentials table (simulates password storage)
CREATE TABLE credentials (
    id SERIAL PRIMARY KEY,
    service VARCHAR(100),
    username VARCHAR(100),
    password VARCHAR(255),
    notes TEXT
);

-- Insert sample data
INSERT INTO users (username, email, department) VALUES
('alice', 'alice@corp.local', 'IT'),
('bob', 'bob@corp.local', 'Sales'),
('Administrator', 'admin@corp.local', 'IT');

-- Insert some credentials (demonstrates lateral movement opportunities)
INSERT INTO credentials (service, username, password, notes) VALUES
('File Server', 'svc_web', 'ServiceWeb123', 'Service account for web application'),
('SQL Server', 'svc_sql', 'SQLService456', 'Database service account'),
('Backup System', 'backup_admin', 'Backup2023!', 'Legacy backup service'),
('VPN', 'alice', 'Alice123!', 'VPN access credentials');
