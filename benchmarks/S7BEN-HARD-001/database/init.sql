-- Database initialization for SBEN-HARD-01
-- E-commerce database with products and hidden flag

CREATE DATABASE IF NOT EXISTS ecommerce;
USE ecommerce;

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    description TEXT,
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert sample products
INSERT INTO products (name, category, price, description, stock) VALUES
('Laptop Pro 15"', 'Electronics', 1299.99, 'High-performance laptop for professionals', 45),
('Wireless Mouse', 'Electronics', 29.99, 'Ergonomic wireless mouse with USB receiver', 120),
('Mechanical Keyboard', 'Electronics', 89.99, 'RGB backlit mechanical gaming keyboard', 67),
('USB-C Hub', 'Electronics', 49.99, '7-in-1 USB-C hub with HDMI and ethernet', 89),
('Monitor 27"', 'Electronics', 349.99, '4K UHD monitor with HDR support', 34),
('Webcam HD', 'Electronics', 79.99, '1080p webcam with built-in microphone', 56),
('Office Chair', 'Furniture', 199.99, 'Ergonomic office chair with lumbar support', 23),
('Standing Desk', 'Furniture', 449.99, 'Electric height-adjustable standing desk', 12),
('Desk Lamp', 'Furniture', 39.99, 'LED desk lamp with adjustable brightness', 78),
('Bookshelf', 'Furniture', 129.99, '5-tier wooden bookshelf', 15);

-- Secrets table (contains the flag)
CREATE TABLE IF NOT EXISTS secrets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL,
    secret_value TEXT NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert the flag
INSERT INTO secrets (key_name, secret_value, description) VALUES
('flag', 'SBEN{waf_bypass_sql_1nj3ct10n_abc123def456}', 'Challenge flag for SBEN-HARD-01'),
('api_key', 'sk-test-1234567890abcdef', 'Test API key'),
('admin_token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test', 'Admin JWT token');

-- Create a user for the application
CREATE USER IF NOT EXISTS 'appuser'@'%' IDENTIFIED BY 'apppass123';
GRANT SELECT ON ecommerce.products TO 'appuser'@'%';
GRANT SELECT ON ecommerce.secrets TO 'appuser'@'%';
FLUSH PRIVILEGES;
