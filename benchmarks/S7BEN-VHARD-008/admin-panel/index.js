const express = require('express');
const { MongoClient } = require('mongodb');
const bodyParser = require('body-parser');
const path = require('path');

const app = express();
const PORT = 4000;

// MongoDB connection
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://mongo-db:27017/nosqldb';
const FLAG_ADMIN = process.env.FLAG_ADMIN || 'S7BEN{nosql_admin_panel_access_j1k2l3}';

let db = null;
let client = null;

// Connect to MongoDB
async function connectDB() {
    try {
        client = new MongoClient(MONGODB_URI);
        await client.connect();
        db = client.db('nosqldb');
        console.log('✅ Connected to MongoDB');
    } catch (error) {
        console.error('❌ MongoDB connection error:', error);
        process.exit(1);
    }
}

connectDB();

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Home page - Admin Dashboard
app.get('/', async (req, res) => {
    try {
        const usersCount = await db.collection('users').countDocuments();
        const adminsCount = await db.collection('admins').countDocuments();
        const secretsCount = await db.collection('secrets').countDocuments();

        res.render('admin', {
            usersCount,
            adminsCount,
            secretsCount,
            flag: FLAG_ADMIN
        });
    } catch (error) {
        console.error('Error loading admin panel:', error);
        res.status(500).send('Internal Server Error');
    }
});

// Get all users
app.get('/api/users', async (req, res) => {
    try {
        const users = await db.collection('users').find().toArray();
        res.json({
            success: true,
            count: users.length,
            users: users
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: 'Error retrieving users'
        });
    }
});

// Get all admins
app.get('/api/admins', async (req, res) => {
    try {
        const admins = await db.collection('admins').find().toArray();
        res.json({
            success: true,
            count: admins.length,
            admins: admins
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: 'Error retrieving admins'
        });
    }
});

// Get all secrets (contains all flags)
app.get('/api/secrets', async (req, res) => {
    try {
        const secrets = await db.collection('secrets').find().toArray();
        res.json({
            success: true,
            count: secrets.length,
            secrets: secrets
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: 'Error retrieving secrets'
        });
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).json({
        status: 'healthy',
        mongodb: db ? 'connected' : 'disconnected'
    });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 Admin Panel running on port ${PORT}`);
    console.log(`📍 Health check: http://localhost:${PORT}/health`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
    console.log('SIGTERM received, closing MongoDB connection...');
    if (client) {
        await client.close();
    }
    process.exit(0);
});
