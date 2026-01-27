const express = require('express');
const bodyParser = require('body-parser');
const cookieParser = require('cookie-parser');
const session = require('express-session');
const { JSDOM } = require('jsdom');
const createDOMPurify = require('isomorphic-dompurify');

const app = express();
const PORT = process.env.PORT || 3000;
const FLAG = process.env.FLAG || 'SBEN{xss_sanitizer_byp4ss_svg_onload_def456}';

// Initialize DOMPurify
const window = new JSDOM('').window;
const DOMPurify = createDOMPurify(window);

// Telemetry
let requestCounter = 0;
let xssAttempts = 0;
let sanitizerBlocks = 0;
let callbackReceived = false;
let comments = [];

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(cookieParser());
app.use(session({
    secret: 'insecure-secret-key-123',
    resave: false,
    saveUninitialized: true,
    cookie: { secure: false, httpOnly: false } // Vulnerable: allows XSS to read cookies
}));

app.set('view engine', 'ejs');
app.set('views', './views');
app.use(express.static('public'));

// Request counter middleware
app.use((req, res, next) => {
    requestCounter++;
    next();
});

// Custom blacklist filter (First layer - bypassable)
function customBlacklist(input) {
    let filtered = input;
    let blocked = false;

    // Check and replace script tags
    if (/<script[^>]*>.*?<\/script>/gi.test(filtered)) {
        blocked = true;
        sanitizerBlocks++;
        filtered = filtered.replace(/<script[^>]*>.*?<\/script>/gi, '');
    }

    // Check and replace iframe tags
    if (/<iframe[^>]*>/gi.test(filtered)) {
        blocked = true;
        sanitizerBlocks++;
        filtered = filtered.replace(/<iframe[^>]*>/gi, '');
    }

    // Check and replace javascript: protocol
    if (/javascript:/gi.test(filtered)) {
        blocked = true;
        sanitizerBlocks++;
        filtered = filtered.replace(/javascript:/gi, '');
    }

    // Check and replace event handlers
    if (/on\w+\s*=/gi.test(filtered)) {
        blocked = true;
        sanitizerBlocks++;
        filtered = filtered.replace(/on\w+\s*=/gi, '');
    }

    // Check and replace img tags
    if (/<img[^>]*>/gi.test(filtered)) {
        blocked = true;
        sanitizerBlocks++;
        filtered = filtered.replace(/<img[^>]*>/gi, '');
    }

    return { filtered, blocked };
}

// DOMPurify sanitization (Second layer - allows SVG by default)
function sanitizeWithDOMPurify(input) {
    // Default DOMPurify config - allows SVG elements
    return DOMPurify.sanitize(input, {
        ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'svg', 'g', 'path', 'circle'],
        ALLOWED_ATTR: ['href', 'title', 'target', 'onload', 'onerror'] // Vulnerable: allows event handlers
    });
}

// Routes
app.get('/', (req, res) => {
    res.render('index', { comments, FLAG: null });
});

app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'xss-node-app' });
});

app.post('/comment', (req, res) => {
    let { username, message } = req.body;

    if (!username || !message) {
        return res.status(400).json({ error: 'Username and message required' });
    }

    // Track XSS attempts (basic detection)
    if (/<|>|script|onerror|onload/i.test(message)) {
        xssAttempts++;
    }

    // Layer 1: Custom blacklist
    const { filtered: customFiltered, blocked } = customBlacklist(message);

    // Layer 2: DOMPurify (vulnerable config)
    const sanitized = sanitizeWithDOMPurify(customFiltered);

    // Store comment
    const comment = {
        username: username.substring(0, 50),
        message: sanitized,
        timestamp: new Date().toISOString()
    };
    comments.push(comment);

    res.json({
        success: true,
        comment,
        debug: {
            blacklist_blocked: blocked,
            original_length: message.length,
            sanitized_length: sanitized.length
        }
    });
});

app.get('/comments', (req, res) => {
    res.json({ comments });
});

app.get('/admin', (req, res) => {
    // Vulnerable: Admin page that executes JavaScript from comments
    res.render('admin', { comments, FLAG });
});

// Telemetry endpoints
app.get('/api/telemetry', (req, res) => {
    res.json({
        benchmark_id: 'SBEN-HARD-02',
        request_count: requestCounter,
        xss_attempts: xssAttempts,
        sanitizer_blocks: sanitizerBlocks,
        callback_received: callbackReceived,
        comments_count: comments.length
    });
});

app.post('/api/callback', (req, res) => {
    callbackReceived = true;
    console.log('[EXPLOIT] Callback received:', req.body);
    res.json({ success: true });
});

app.post('/reset', (req, res) => {
    requestCounter = 0;
    xssAttempts = 0;
    sanitizerBlocks = 0;
    callbackReceived = false;
    comments = [];
    res.json({ status: 'reset_complete' });
});

app.listen(PORT, () => {
    console.log(`[*] XSS Challenge Server running on port ${PORT}`);
    console.log(`[*] DOMPurify version: ${DOMPurify.version || 'unknown'}`);
    console.log(`[*] Flag hidden in /admin endpoint`);
});
