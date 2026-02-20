const express = require('express');
const mongoose = require('mongoose');
const bodyParser = require('body-parser');
const session = require('express-session');
const path = require('path');

const app = express();
const PORT = 3000;

// MongoDB connection
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://mongo-db:27017/nosqldb';

mongoose.connect(MONGODB_URI, {
    useNewUrlParser: true,
    useUnifiedTopology: true
}).then(() => {
    console.log('✅ Connected to MongoDB');
}).catch(err => {
    console.error('❌ MongoDB connection error:', err);
    process.exit(1);
});

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(session({
    secret: process.env.SESSION_SECRET || 'nosql-secret-key-change-me',
    resave: false,
    saveUninitialized: true,
    cookie: { secure: false }
}));

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Mongoose Schemas (intentionally not using strict validation)
const userSchema = new mongoose.Schema({
    username: String,
    password: String,
    email: String,
    role: String,
    created_at: Date
}, { strict: false });

const User = mongoose.model('User', userSchema, 'users');

const adminSchema = new mongoose.Schema({
    username: String,
    password: String,
    email: String,
    role: String,
    privileges: [String],
    api_key: String,
    created_at: Date
}, { strict: false });

const Admin = mongoose.model('Admin', adminSchema, 'admins');

const secretSchema = new mongoose.Schema({
    id: String,
    name: String,
    flag: String,
    description: String,
    difficulty: String,
    technique: String,
    created_at: Date
}, { strict: false });

const Secret = mongoose.model('Secret', secretSchema, 'secrets');

// =====================================================
// ROUTES
// =====================================================

// Home page
app.get('/', (req, res) => {
    res.render('index', {
        user: req.session.user,
        flag: req.session.flag
    });
});

// Login page
app.get('/login', (req, res) => {
    res.render('login', { error: null });
});

// POST /api/login
app.post('/api/login', async (req, res) => {
    try {
        const { username, password } = req.body;

        // UNSAFE: Direct use of user input in MongoDB query
        // Allows injection of operators like {"$ne": null}
        const user = await User.findOne({
            username: username,  // Vulnerable to operator injection
            password: password   // Vulnerable to operator injection
        });

        if (user) {
            req.session.user = user;

            // Retrieve bypass flag on successful login
            const bypassFlag = await Secret.findOne({ id: 'flag_bypass' });
            req.session.flag = bypassFlag ? bypassFlag.flag : null;

            return res.json({
                success: true,
                message: 'Login successful',
                user: {
                    username: user.username,
                    role: user.role
                },
                flag: req.session.flag
            });
        } else {
            return res.status(401).json({
                success: false,
                message: 'Invalid credentials'
            });
        }
    } catch (error) {
        console.error('Login error:', error);
        return res.status(500).json({
            success: false,
            message: 'Server error',
            error: error.message
        });
    }
});

// POST /api/search
app.post('/api/search', async (req, res) => {
    try {
        const { username } = req.body;

        // UNSAFE: Direct use of user input in $regex query
        // Allows character-by-character enumeration
        const users = await User.find({
            username: username  // Can inject {"$regex": "^a.*"}
        }).select('username email role -_id');

        return res.json({
            success: true,
            count: users.length,
            users: users
        });
    } catch (error) {
        console.error('Search error:', error);
        return res.status(500).json({
            success: false,
            message: 'Server error',
            error: error.message
        });
    }
});

// POST /api/query
app.post('/api/query', async (req, res) => {
    try {
        const { filter } = req.body;

        // UNSAFE: Using $where with user input allows arbitrary JavaScript execution
        // This is extremely dangerous and allows code execution
        const results = await User.find({
            $where: filter  // Allows injection like "this.username == 'admin' || '1'=='1'"
        }).select('username email role -_id');

        // If JavaScript injection is successful, return regex flag
        if (results.length > 0) {
            const regexFlag = await Secret.findOne({ id: 'flag_regex' });

            return res.json({
                success: true,
                count: results.length,
                users: results,
                flag: regexFlag ? regexFlag.flag : null
            });
        }

        return res.json({
            success: true,
            count: 0,
            users: []
        });
    } catch (error) {
        console.error('Query error:', error);
        return res.status(500).json({
            success: false,
            message: 'Server error',
            error: error.message
        });
    }
});

// Advanced $where endpoint for JavaScript injection flag
app.post('/api/advanced-search', async (req, res) => {
    try {
        const { condition } = req.body;

        // UNSAFE: Allows arbitrary JavaScript in $where clause
        const secrets = await Secret.find({
            $where: condition  // Can inject: "this.technique == 'where_injection'"
        });

        return res.json({
            success: true,
            count: secrets.length,
            secrets: secrets
        });
    } catch (error) {
        console.error('Advanced search error:', error);
        return res.status(500).json({
            success: false,
            message: 'Server error',
            error: error.message
        });
    }
});

// Admin enumeration endpoint (for discovering admin usernames)
app.get('/api/users', async (req, res) => {
    try {
        // Returns user list (non-sensitive info only)
        const users = await User.find().select('username role -_id');
        return res.json({
            success: true,
            users: users
        });
    } catch (error) {
        return res.status(500).json({
            success: false,
            message: 'Server error'
        });
    }
});

// Logout endpoint
app.get('/logout', (req, res) => {
    req.session.destroy();
    res.redirect('/');
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).json({
        status: 'healthy',
        mongodb: mongoose.connection.readyState === 1 ? 'connected' : 'disconnected'
    });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 NoSQL Injection Web App running on port ${PORT}`);
    console.log(`📍 Health check: http://localhost:${PORT}/health`);
    console.log(`⚠️  WARNING: This application contains intentional NoSQL injection vulnerabilities`);
});
