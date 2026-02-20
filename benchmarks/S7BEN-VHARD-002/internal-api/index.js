const express = require('express');
const app = express();
const PORT = 3000;

app.use(express.json());

/**
 * Internal API Service
 * Provides redirect endpoints that can bypass SSRF filters
 */

// Health check
app.get('/health', (req, res) => {
    res.status(200).send('healthy');
});

/**
 * Open redirect endpoint
 * Can be used to bypass SSRF filters through redirect chaining
 */
app.get('/redirect', (req, res) => {
    const target = req.query.url || req.query.target;

    if (!target) {
        return res.status(400).json({
            error: 'Missing url parameter',
            usage: '/redirect?url=http://example.com'
        });
    }

    // Allows redirecting to internal services
    res.redirect(302, target);
});

/**
 * Service discovery endpoint
 */
app.get('/services', (req, res) => {
    res.json({
        available_services: [
            {
                name: 'metadata-service',
                host: '169.254.169.254',
                description: 'Cloud metadata service',
                endpoints: [
                    '/latest/meta-data/',
                    '/latest/user-data',
                    '/latest/meta-data/iam/security-credentials/'
                ]
            },
            {
                name: 'admin-panel',
                host: 'admin-panel:4000',
                description: 'Admin control panel (requires AWS credentials)',
                auth: 'AWS SigV4 or AccessKey header'
            },
            {
                name: 'internal-api',
                host: 'internal-api:3000',
                description: 'Internal API gateway',
                note: 'You are here'
            }
        ],
        hint: 'Use /redirect endpoint to reach internal services'
    });
});

/**
 * Status endpoint with sensitive information
 */
app.get('/status', (req, res) => {
    res.json({
        service: 'internal-api',
        version: '1.0.0',
        environment: 'production',
        internal_services: {
            metadata: 'http://169.254.169.254',
            admin: 'http://admin-panel:4000'
        },
        hint: 'Metadata service contains AWS credentials'
    });
});

/**
 * Debug endpoint (should not be exposed)
 */
app.get('/debug/headers', (req, res) => {
    res.json({
        headers: req.headers,
        ip: req.ip,
        method: req.method,
        url: req.url
    });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`[*] Internal API service listening on port ${PORT}`);
});
