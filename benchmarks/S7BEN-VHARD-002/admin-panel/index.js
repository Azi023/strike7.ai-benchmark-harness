const express = require('express');
const crypto = require('crypto');
const app = express();
const PORT = 4000;

app.use(express.json());

// Expected AWS credentials (from metadata service)
const VALID_ACCESS_KEY = process.env.AWS_ACCESS_KEY_ID || 'AKIAIOSFODNN7EXAMPLE';
const FLAG = process.env.FLAG || 'SBEN{admin_access_via_ssrf_credentials}';

/**
 * Admin Panel Service
 * Requires AWS credentials obtained from metadata service
 */

// Health check
app.get('/health', (req, res) => {
    res.status(200).send('healthy');
});

/**
 * Simple authentication check
 * Accepts AWS Access Key in header
 */
function authenticateRequest(req, res, next) {
    const accessKey = req.headers['x-aws-access-key'] ||
                      req.headers['authorization']?.replace('AWS ', '');

    if (!accessKey) {
        return res.status(401).json({
            error: 'Authentication required',
            message: 'Provide X-AWS-Access-Key header with valid AWS credentials',
            hint: 'AWS credentials can be found in cloud metadata service'
        });
    }

    // Simple validation (just check if it matches)
    if (accessKey !== VALID_ACCESS_KEY) {
        return res.status(403).json({
            error: 'Invalid credentials',
            message: 'Access key does not match',
            received: accessKey.substring(0, 10) + '...'
        });
    }

    next();
}

/**
 * Public endpoint - shows authentication requirements
 */
app.get('/', (req, res) => {
    res.json({
        service: 'Admin Control Panel',
        version: '2.0.0',
        authentication: {
            required: true,
            method: 'AWS Access Key',
            header: 'X-AWS-Access-Key',
            example: 'X-AWS-Access-Key: AKIA...'
        },
        endpoints: {
            '/admin/flag': 'Retrieve the final flag (requires auth)',
            '/admin/config': 'View system configuration (requires auth)',
            '/admin/users': 'List admin users (requires auth)'
        },
        hint: 'Credentials can be obtained from EC2 metadata service at 169.254.169.254'
    });
});

/**
 * Admin flag endpoint (main target)
 * Requires valid AWS credentials from metadata service
 */
app.get('/admin/flag', authenticateRequest, (req, res) => {
    res.json({
        success: true,
        message: 'Successfully authenticated with AWS credentials',
        flag: FLAG,
        note: 'Congratulations! You successfully exploited SSRF to access cloud metadata and retrieved admin credentials'
    });
});

/**
 * Admin configuration endpoint
 */
app.get('/admin/config', authenticateRequest, (req, res) => {
    res.json({
        application: {
            name: 'ProductionApp',
            version: '3.2.1',
            environment: 'production'
        },
        database: {
            host: 'prod-db.internal',
            port: 5432,
            name: 'main_db',
            user: 'db_admin'
        },
        secrets: {
            api_key: 'sk-prod-' + crypto.randomBytes(16).toString('hex'),
            webhook_secret: 'whsec_' + crypto.randomBytes(20).toString('hex'),
            encryption_key: crypto.randomBytes(32).toString('hex')
        },
        aws: {
            region: 'us-east-1',
            account_id: '123456789012',
            role: 'WebServerRole'
        }
    });
});

/**
 * Admin users list
 */
app.get('/admin/users', authenticateRequest, (req, res) => {
    res.json({
        total: 3,
        users: [
            {
                id: 1,
                username: 'admin',
                role: 'super_admin',
                email: 'admin@company.com',
                last_login: '2026-01-12T10:30:00Z'
            },
            {
                id: 2,
                username: 'devops',
                role: 'admin',
                email: 'devops@company.com',
                last_login: '2026-01-12T09:15:00Z'
            },
            {
                id: 3,
                username: 'security',
                role: 'auditor',
                email: 'security@company.com',
                last_login: '2026-01-11T14:20:00Z'
            }
        ]
    });
});

/**
 * System status (authenticated)
 */
app.get('/admin/status', authenticateRequest, (req, res) => {
    res.json({
        status: 'operational',
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        timestamp: new Date().toISOString(),
        services: {
            database: 'connected',
            cache: 'operational',
            queue: 'processing'
        }
    });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`[*] Admin panel listening on port ${PORT}`);
    console.log(`[*] Required AWS Access Key: ${VALID_ACCESS_KEY.substring(0, 10)}...`);
});
