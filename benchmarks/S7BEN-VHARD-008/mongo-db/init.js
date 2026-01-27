// MongoDB initialization script for SBEN-NOSQL-01
// Creates collections and seeds data with vulnerabilities

db = db.getSiblingDB('nosqldb');

// Drop existing collections if they exist
db.users.drop();
db.admins.drop();
db.secrets.drop();

print('Creating users collection...');

// Create users collection with regular users
db.users.insertMany([
    {
        username: 'alice',
        password: 'alice123',
        email: 'alice@example.com',
        role: 'user',
        created_at: new Date()
    },
    {
        username: 'bob',
        password: 'bob456',
        email: 'bob@example.com',
        role: 'user',
        created_at: new Date()
    },
    {
        username: 'charlie',
        password: 'charlie789',
        email: 'charlie@example.com',
        role: 'user',
        created_at: new Date()
    },
    {
        username: 'guest',
        password: 'guest',
        email: 'guest@example.com',
        role: 'guest',
        created_at: new Date()
    }
]);

print('Creating admins collection...');

// Create admins collection with privileged users
db.admins.insertMany([
    {
        username: 'admin',
        password: 'admin_secret_p@ssw0rd',
        email: 'admin@corp.local',
        role: 'administrator',
        privileges: ['read', 'write', 'delete', 'admin'],
        api_key: 'admin-api-key-12345',
        created_at: new Date()
    },
    {
        username: 'superadmin',
        password: 'super_secret_p@ssw0rd_2024',
        email: 'superadmin@corp.local',
        role: 'superadministrator',
        privileges: ['read', 'write', 'delete', 'admin', 'root'],
        api_key: 'superadmin-api-key-67890',
        created_at: new Date()
    }
]);

print('Creating secrets collection...');

// Create secrets collection with flags
// Flags will be retrieved through different NoSQL injection techniques
db.secrets.insertMany([
    {
        id: 'flag_bypass',
        name: 'Authentication Bypass Flag',
        flag: process.env.FLAG_BYPASS || 'SBEN{nosql_auth_bypass_ne_operator_a1b2c3}',
        description: 'Retrieved via $ne operator authentication bypass',
        difficulty: 'easy',
        technique: 'ne_operator',
        created_at: new Date()
    },
    {
        id: 'flag_regex',
        name: 'Regex Extraction Flag',
        flag: process.env.FLAG_REGEX || 'SBEN{nosql_regex_data_extraction_d4e5f6}',
        description: 'Retrieved via $regex operator for data extraction',
        difficulty: 'medium',
        technique: 'regex_injection',
        created_at: new Date()
    },
    {
        id: 'flag_where',
        name: 'JavaScript Injection Flag',
        flag: process.env.FLAG_WHERE || 'SBEN{nosql_where_javascript_injection_g7h8i9}',
        description: 'Retrieved via $where clause JavaScript injection',
        difficulty: 'hard',
        technique: 'where_injection',
        created_at: new Date()
    }
]);

// Create indexes
db.users.createIndex({ username: 1 }, { unique: true });
db.admins.createIndex({ username: 1 }, { unique: true });
db.secrets.createIndex({ id: 1 }, { unique: true });

print('Database initialization complete!');
print('Users collection: ' + db.users.countDocuments());
print('Admins collection: ' + db.admins.countDocuments());
print('Secrets collection: ' + db.secrets.countDocuments());
