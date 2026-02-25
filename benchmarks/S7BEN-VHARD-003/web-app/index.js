const express = require('express');
const session = require('express-session');
const bodyParser = require('body-parser');
const ldap = require('ldapjs');

const app = express();
const PORT = 3000;

// Configuration
const LDAP_URL = process.env.LDAP_URL || 'ldap://dc.corp.local:389';
const DOMAIN = process.env.DOMAIN || 'CORP.LOCAL';
const BASE_DN = 'dc=corp,dc=local';
const FLAG_KERBEROAST = process.env.FLAG_KERBEROAST || 'SBEN{kerberoast_service_account_a7b3c9d1e5f2g8h4}';

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(session({
    secret: 'webapp-session-secret-key',
    resave: false,
    saveUninitialized: false,
    cookie: { secure: false }
}));

// LDAP client
function createLdapClient() {
    return ldap.createClient({
        url: LDAP_URL,
        timeout: 5000,
        connectTimeout: 10000
    });
}

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'web-app' });
});

// Home page
app.get('/', (req, res) => {
    if (req.session.user) {
        res.json({
            message: 'Welcome to Corporate Portal',
            user: req.session.user,
            links: {
                profile: '/api/profile',
                services: '/api/services',
                logout: '/api/logout'
            }
        });
    } else {
        res.json({
            message: 'Corporate Portal - Please Login',
            endpoints: {
                login: 'POST /api/login',
                info: 'GET /api/info'
            }
        });
    }
});

// Login endpoint with LDAP authentication
app.post('/api/login', async (req, res) => {
    const { username, password } = req.body;

    if (!username || !password) {
        return res.status(400).json({ error: 'Username and password required' });
    }

    const client = createLdapClient();

    try {
        // First, search for the user
        const searchDN = BASE_DN;
        const searchFilter = `(uid=${username})`;

        // Anonymous bind for search
        await new Promise((resolve, reject) => {
            client.bind('', '', (err) => {
                if (err) reject(err);
                else resolve();
            });
        });

        // Search for user
        const searchResults = await new Promise((resolve, reject) => {
            const entries = [];
            client.search(searchDN, { filter: searchFilter, scope: 'sub' }, (err, searchRes) => {
                if (err) {
                    reject(err);
                    return;
                }

                searchRes.on('searchEntry', (entry) => {
                    entries.push(entry);
                });

                searchRes.on('error', (err) => {
                    reject(err);
                });

                searchRes.on('end', () => {
                    resolve(entries);
                });
            });
        });

        if (searchResults.length === 0) {
            client.unbind();
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        const userEntry = searchResults[0];
        const userDN = userEntry.objectName;

        // Try to bind with user credentials
        const authClient = createLdapClient();
        await new Promise((resolve, reject) => {
            authClient.bind(userDN, password, (err) => {
                if (err) reject(err);
                else resolve();
            });
        });

        // Authentication successful
        const userInfo = {
            username: username,
            dn: userDN,
            cn: userEntry.object.cn,
            mail: userEntry.object.mail || `${username}@corp.local`
        };

        req.session.user = userInfo;

        authClient.unbind();
        client.unbind();

        res.json({
            message: 'Login successful',
            user: userInfo
        });

    } catch (error) {
        client.unbind();
        console.error('Login error:', error);
        res.status(401).json({ error: 'Invalid credentials' });
    }
});

// Profile endpoint
app.get('/api/profile', (req, res) => {
    if (!req.session.user) {
        return res.status(401).json({ error: 'Not authenticated' });
    }

    res.json({
        profile: req.session.user,
        message: 'User profile information'
    });
});

// Services endpoint
app.get('/api/services', (req, res) => {
    if (!req.session.user) {
        return res.status(401).json({ error: 'Not authenticated' });
    }

    res.json({
        message: 'Corporate Services',
        services: [
            {
                name: 'Web Application',
                spn: 'HTTP/webapp.corp.local',
                account: 'svc_web@CORP.LOCAL',
                status: 'running',
                description: 'Main corporate web portal'
            },
            {
                name: 'Database Server',
                spn: 'MSSQLSvc/dbserver.corp.local',
                account: 'svc_sql@CORP.LOCAL',
                status: 'running',
                description: 'Corporate SQL Server'
            }
        ]
    });
});

// Admin endpoint - requires Administrator
app.get('/api/admin/flag', (req, res) => {
    if (!req.session.user) {
        return res.status(401).json({ error: 'Not authenticated' });
    }

    const username = req.session.user.username;

    if (username !== 'Administrator' && username !== 'administrator') {
        return res.status(403).json({
            error: 'Access denied',
            message: 'This endpoint requires Administrator privileges'
        });
    }

    res.json({
        message: 'Administrator access granted',
        flag: FLAG_KERBEROAST
    });
});

// Logout
app.post('/api/logout', (req, res) => {
    req.session.destroy();
    res.json({ message: 'Logged out successfully' });
});

// Info endpoint
app.get('/api/info', (req, res) => {
    res.json({
        application: 'Corporate Portal',
        domain: DOMAIN,
        ldap_server: LDAP_URL,
        authentication: 'LDAP',
        features: {
            login: 'POST /api/login',
            profile: 'GET /api/profile (authenticated)',
            services: 'GET /api/services (authenticated)',
            admin: 'GET /api/admin/flag (Administrator only)'
        }
    });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`[+] Web application listening on port ${PORT}`);
    console.log(`[+] LDAP URL: ${LDAP_URL}`);
    console.log(`[+] Domain: ${DOMAIN}`);
});
