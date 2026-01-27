const express = require('express');
const bodyParser = require('body-parser');

const app = express();
const PORT = process.env.PORT || 8080;

let callbacks = [];
let exploitSuccessful = false;

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// CORS for cross-origin requests
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type');
    next();
});

app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'callback-server' });
});

// Callback endpoint - receives exfiltrated data
app.all('/callback', (req, res) => {
    const callback = {
        timestamp: new Date().toISOString(),
        method: req.method,
        headers: req.headers,
        query: req.query,
        body: req.body,
        ip: req.ip
    };

    callbacks.push(callback);
    exploitSuccessful = true;

    console.log('[EXPLOIT SUCCESS] Callback received:');
    console.log(`  Method: ${req.method}`);
    console.log(`  Headers:`, JSON.stringify(req.headers, null, 2));
    console.log(`  Query:`, JSON.stringify(req.query, null, 2));
    console.log(`  Body:`, JSON.stringify(req.body, null, 2));

    res.json({
        success: true,
        message: 'Callback received',
        exploit_successful: true
    });
});

// Exfiltration endpoint - alternative to /callback
app.get('/exfil', (req, res) => {
    const data = {
        timestamp: new Date().toISOString(),
        data: req.query.data || req.query.d || 'no data',
        cookie: req.query.cookie || req.query.c || 'no cookie',
        flag: req.query.flag || req.query.f || 'no flag'
    };

    callbacks.push(data);
    exploitSuccessful = true;

    console.log('[EXFILTRATION] Data received:', data);

    // Return 1x1 transparent pixel for image-based exfil
    res.writeHead(200, {
        'Content-Type': 'image/gif',
        'Content-Length': 43
    });
    res.end(Buffer.from('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7', 'base64'));
});

// Status endpoint
app.get('/status', (req, res) => {
    res.json({
        exploit_successful: exploitSuccessful,
        callbacks_received: callbacks.length,
        callbacks: callbacks.slice(-10) // Last 10 callbacks
    });
});

// Reset endpoint
app.post('/reset', (req, res) => {
    callbacks = [];
    exploitSuccessful = false;
    console.log('[RESET] Callback server reset');
    res.json({ status: 'reset_complete' });
});

app.listen(PORT, () => {
    console.log(`[*] Callback server running on port ${PORT}`);
    console.log(`[*] Waiting for exploit callbacks...`);
});
