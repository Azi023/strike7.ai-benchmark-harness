<?php
require_once __DIR__ . '/patch.php';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ContentHub Platform</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f1117;
            color: #e4e4e7;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .container {
            text-align: center;
            max-width: 480px;
            padding: 2rem;
        }
        .logo {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle {
            color: #71717a;
            font-size: 1rem;
            margin-bottom: 2.5rem;
        }
        .actions {
            display: flex;
            gap: 1rem;
            justify-content: center;
        }
        .btn {
            display: inline-block;
            padding: 0.75rem 1.75rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            font-size: 0.95rem;
            transition: all 0.2s;
        }
        .btn-primary {
            background: #6366f1;
            color: #fff;
        }
        .btn-primary:hover { background: #4f46e5; }
        .btn-secondary {
            background: #27272a;
            color: #e4e4e7;
            border: 1px solid #3f3f46;
        }
        .btn-secondary:hover { background: #3f3f46; }
        .footer {
            margin-top: 3rem;
            color: #52525b;
            font-size: 0.8rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">ContentHub</div>
        <p class="subtitle">Enterprise Content Management Platform</p>
        <div class="actions">
            <a href="/login.php" class="btn btn-primary">Sign In</a>
            <a href="/docs.php" class="btn btn-secondary">API Reference</a>
        </div>
        <p class="footer">ContentHub Platform v3.2.1</p>
    </div>
</body>
</html>
