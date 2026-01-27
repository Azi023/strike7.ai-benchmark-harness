const express = require('express');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const bodyParser = require('body-parser');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Configuration
const JWT_SECRET = process.env.JWT_SECRET || 'default-jwt-secret-change-me';
const FLAG_SECRET = process.env.FLAG_SECRET || 'strike7-chain01-secret';

// Generate RSA key pair on startup (for JWT algorithm confusion vuln)
let publicKey, privateKey;

function loadOrGenerateKeyPair() {
    const keysDir = '/app/keys';
    const publicKeyPath = path.join(keysDir, 'public.pem');
    const privateKeyPath = path.join(keysDir, 'private.pem');

    // Try to load existing keys first
    if (fs.existsSync(publicKeyPath) && fs.existsSync(privateKeyPath)) {
        try {
            publicKey = fs.readFileSync(publicKeyPath, 'utf8').trimEnd() + '\n';
            privateKey = fs.readFileSync(privateKeyPath, 'utf8').trimEnd() + '\n';
            console.log('[+] Loaded existing RSA key pair from volume');
            return;
        } catch (err) {
            console.log('[!] Error loading keys, generating new pair:', err.message);
        }
    }

    // Generate new keys if they don't exist
    const { publicKey: pubKey, privateKey: privKey } = crypto.generateKeyPairSync('rsa', {
        modulusLength: 2048,
        publicKeyEncoding: {
            type: 'spki',
            format: 'pem'
        },
        privateKeyEncoding: {
            type: 'pkcs8',
            format: 'pem'
        }
    });

    // Normalize keys to ensure consistent trailing newlines
    publicKey = pubKey.trimEnd() + '\n';
    privateKey = privKey.trimEnd() + '\n';

    // Save keys to filesystem
    if (!fs.existsSync(keysDir)) {
        fs.mkdirSync(keysDir, { recursive: true });
    }
    fs.writeFileSync(publicKeyPath, publicKey);
    fs.writeFileSync(privateKeyPath, privateKey);

    console.log('[+] Generated and saved new RSA key pair');
}

loadOrGenerateKeyPair();

// Mock users database
const USERS = {
    'user': {
        password: 'userpass',
        role: 'user',
        email: 'user@example.com'
    },
    'admin': {
        password: 'AdminSecurePass123!',
        role: 'admin',
        email: 'admin@example.com'
    }
};

// Health check
app.get('/health', (req, res) => {
    res.status(200).send('healthy');
});

// Login endpoint
app.post('/login', (req, res) => {
    const { username, password } = req.body;

    if (!username || !password) {
        return res.status(400).json({
            error: 'Username and password required'
        });
    }

    const user = USERS[username];

    if (!user || user.password !== password) {
        return res.status(401).json({
            error: 'Invalid credentials'
        });
    }

    // Generate JWT token using RS256
    const payload = {
        username: username,
        role: user.role,
        email: user.email,
        iat: Math.floor(Date.now() / 1000)
    };

    const token = jwt.sign(payload, privateKey, {
        algorithm: 'RS256',
        expiresIn: '24h'
    });

    res.json({
        status: 'success',
        token: token,
        user: {
            username: username,
            role: user.role,
            email: user.email
        }
    });
});

// Verify token endpoint
app.post('/verify', (req, res) => {
    const token = req.headers.authorization?.replace('Bearer ', '') || req.body.token;

    if (!token) {
        return res.status(400).json({
            error: 'Token required'
        });
    }

    try {
        // VULNERABILITY: Algorithm confusion attack
        // Decode header to check algorithm (without verification)
        const decodedHeader = jwt.decode(token, { complete: true });

        if (!decodedHeader) {
            return res.status(401).json({
                error: 'Invalid token',
                message: 'Malformed token'
            });
        }

        const algorithm = decodedHeader.header.alg;
        let decoded;

        // VULNERABILITY: Manual verification allows algorithm confusion
        if (algorithm === 'HS256') {
            // For HS256, manually verify using public key as HMAC secret
            // This is the core vulnerability - treating asymmetric key as symmetric
            const parts = token.split('.');
            if (parts.length !== 3) {
                throw new Error('Invalid token format');
            }

            const [headerB64, payloadB64, signatureB64] = parts;
            const signingInput = `${headerB64}.${payloadB64}`;

            // Create HMAC signature using public key as secret
            // IMPORTANT: Must use Buffer.from() to match Python's encoding
            const hmac = crypto.createHmac('sha256', Buffer.from(publicKey, 'utf8'));
            hmac.update(Buffer.from(signingInput, 'utf8'));
            const signature = hmac.digest('base64');

            // Convert to base64url (replace +/= characters)
            const expectedSignature = signature
                .replace(/\+/g, '-')
                .replace(/\//g, '_')
                .replace(/=/g, '');

            // Compare signatures
            if (signatureB64 !== expectedSignature) {
                throw new Error('Invalid signature');
            }

            // Decode payload without verification (already verified above)
            decoded = jwt.decode(token);

        } else if (algorithm === 'none') {
            // Accept 'none' algorithm (another vulnerability)
            decoded = jwt.decode(token);
        } else {
            // For RS256, use normal verification
            decoded = jwt.verify(token, publicKey, {
                algorithms: ['RS256']
            });
        }

        res.json({
            status: 'valid',
            payload: decoded
        });
    } catch (error) {
        res.status(401).json({
            error: 'Invalid token',
            message: error.message
        });
    }
});

// Internal debug endpoint (for SSRF discovery)
// STEP 1 TARGET: This endpoint reveals JWT configuration
app.get('/internal/debug', (req, res) => {
    // This endpoint should only be accessible from internal network
    // But SSRF in api-service can reach it

    res.json({
        service: 'auth-service',
        version: '1.0.0',
        jwt_config: {
            algorithm: 'RS256',
            algorithms_accepted: ['RS256', 'HS256', 'none'],  // VULNERABILITY HINT
            public_key_available: true,
            token_expiry: '24h'
        },
        public_key: publicKey,  // VULNERABILITY: Exposes public key
        endpoints: {
            login: '/login',
            verify: '/verify',
            debug: '/internal/debug'
        },
        note: 'Internal debug endpoint - should not be publicly accessible'
    });
});

// Public key endpoint (for JWT verification)
app.get('/public-key', (req, res) => {
    res.type('text/plain');
    res.send(publicKey);
});

// API documentation
app.get('/docs', (req, res) => {
    res.json({
        service: 'Authentication Service',
        endpoints: [
            {
                method: 'POST',
                path: '/login',
                description: 'Authenticate user and receive JWT token',
                body: { username: 'string', password: 'string' }
            },
            {
                method: 'POST',
                path: '/verify',
                description: 'Verify JWT token validity',
                headers: { authorization: 'Bearer <token>' }
            },
            {
                method: 'GET',
                path: '/public-key',
                description: 'Get RSA public key for JWT verification'
            }
        ]
    });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`[*] Auth service listening on port ${PORT}`);
    console.log(`[*] JWT Secret: ${JWT_SECRET.substring(0, 10)}...`);
    console.log(`[*] Using RS256 algorithm with RSA keys`);
});
