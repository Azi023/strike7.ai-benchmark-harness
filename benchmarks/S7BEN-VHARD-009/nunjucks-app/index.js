const express = require('express');
const nunjucks = require('nunjucks');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 3000;

// Flag file location
const FLAG_FILE = '/app/flag.txt';

// Configure Nunjucks
const env = nunjucks.configure('views', {
    autoescape: false,
    express: app
});

// Middleware
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// Home page route
app.get('/', (req, res) => {
    const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Nunjucks Template Engine</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            width: 100%;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
            text-align: center;
        }
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
        }
        .result {
            background: #e3f2fd;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            word-wrap: break-word;
        }
        .result h2 {
            color: #1976d2;
            margin-bottom: 10px;
        }
        form {
            margin-top: 20px;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            margin-bottom: 15px;
        }
        button {
            width: 100%;
            padding: 14px;
            background: #f5576c;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover {
            background: #e04455;
            transform: translateY(-2px);
        }
        .footer {
            text-align: center;
            margin-top: 20px;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>GreetingCard Generator</h1>
        <p class="subtitle">Personalized greeting card service</p>

        <div class="result">
            <h2>Greeting Result:</h2>
            <p>Welcome! Enter your name below.</p>
        </div>

        <form method="GET" action="/greet">
            <input type="text" name="name" placeholder="Enter your name" required>
            <button type="submit">Generate Greeting</button>
        </form>

        <div class="footer">
            GreetingCard Generator | Powered by template engine
        </div>
    </div>
</body>
</html>
    `;
    res.send(html);
});

// Vulnerable greeting route
app.get('/greet', (req, res) => {
    const name = req.query.name || '';

    if (!name) {
        return res.send('<h1>Please enter a name!</h1><a href="/">Go back</a>');
    }

    const template = `Hello, ${name}!`;

    try {
        // UNSAFE: renderString on user-controlled content
        const output = nunjucks.renderString(template);

        const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Nunjucks Template Engine</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            width: 100%;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
            text-align: center;
        }
        .result {
            background: #e3f2fd;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            word-wrap: break-word;
        }
        .result h2 {
            color: #1976d2;
            margin-bottom: 10px;
        }
        a {
            display: block;
            text-align: center;
            color: #f5576c;
            text-decoration: none;
            font-weight: 600;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Node.js/Nunjucks Template Engine</h1>
        <div class="result">
            <h2>Greeting Result:</h2>
            <p>${output}</p>
        </div>
        <a href="/">← Back to Home</a>
    </div>
</body>
</html>
        `;
        res.send(html);
    } catch (error) {
        res.send(`<h1>Template Error:</h1><pre>${error.message}</pre><a href="/">Go back</a>`);
    }
});

// Alternative direct SSTI testing endpoint
app.get('/test', (req, res) => {
    const template = req.query.template || '{{7*7}}';

    try {
        // UNSAFE: Directly render user-supplied template
        const result = nunjucks.renderString(template);
        res.send(`<h1>Template Result:</h1><pre>${result}</pre>`);
    } catch (error) {
        res.send(`<h1>Template Error:</h1><pre>${error.message}</pre>`);
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        engine: 'Nunjucks',
        language: 'Node.js'
    });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    // Create flag file on startup
    const flagContent = process.env.FLAG_NUNJUCKS || 'SBEN{nunjucks_ssti_nodejs_rce_e5f6g7h8}';

    fs.mkdirSync('/app', { recursive: true });
    fs.writeFileSync(FLAG_FILE, flagContent);

    console.log(`GreetingCard Generator (Nunjucks) running on port ${PORT}`);
});
