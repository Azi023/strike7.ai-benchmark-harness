<?php
require_once __DIR__ . '/patch.php';
require_once __DIR__ . '/classes.php';
session_start();

if (!isset($_SESSION['authenticated']) || $_SESSION['authenticated'] !== true) {
    header('Location: /login.php');
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - ContentHub</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f1117;
            color: #e4e4e7;
            min-height: 100vh;
        }
        .navbar {
            background: #18181b;
            border-bottom: 1px solid #27272a;
            padding: 0.75rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .navbar .brand { font-weight: 600; color: #6366f1; font-size: 1.1rem; }
        .navbar .user { color: #a1a1aa; font-size: 0.85rem; }
        .main { max-width: 720px; margin: 2rem auto; padding: 0 1.5rem; }
        h1 { font-size: 1.5rem; margin-bottom: 1.5rem; }
        .card {
            background: #18181b;
            border: 1px solid #27272a;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .card h2 { font-size: 1.1rem; margin-bottom: 0.75rem; }
        .card p { color: #a1a1aa; font-size: 0.9rem; margin-bottom: 1rem; }
        label { display: block; font-size: 0.85rem; color: #a1a1aa; margin-bottom: 0.25rem; }
        input[type="url"], input[type="text"] {
            width: 100%;
            padding: 0.6rem 0.75rem;
            background: #27272a;
            border: 1px solid #3f3f46;
            border-radius: 6px;
            color: #e4e4e7;
            font-size: 0.9rem;
            margin-bottom: 0.75rem;
        }
        input:focus { outline: none; border-color: #6366f1; }
        .btn {
            padding: 0.6rem 1.25rem;
            background: #6366f1;
            color: #fff;
            border: none;
            border-radius: 6px;
            font-size: 0.9rem;
            cursor: pointer;
        }
        .btn:hover { background: #4f46e5; }
        #result {
            margin-top: 1rem;
            background: #09090b;
            border: 1px solid #27272a;
            border-radius: 6px;
            padding: 1rem;
            font-family: monospace;
            font-size: 0.8rem;
            color: #a1a1aa;
            max-height: 300px;
            overflow: auto;
            display: none;
            white-space: pre-wrap;
            word-break: break-all;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <span class="brand">ContentHub</span>
        <span class="user"><?= htmlspecialchars($_SESSION['username'] ?? 'user') ?></span>
    </div>
    <div class="main">
        <h1>Content Dashboard</h1>
        <div class="card">
            <h2>Link Preview</h2>
            <p>Preview external content by entering a URL below.</p>
            <form id="previewForm">
                <label for="url">URL</label>
                <input type="text" id="url" name="url" placeholder="https://example.com" required>
                <button type="submit" class="btn">Preview</button>
            </form>
            <div id="result"></div>
        </div>
        <div class="card">
            <h2>Quick Links</h2>
            <p>
                <a href="/docs.php" style="color:#6366f1;">API Reference</a> &middot;
                <a href="/status.php" style="color:#6366f1;">Platform Status</a>
            </p>
        </div>
    </div>
    <script>
        document.getElementById('previewForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const url = document.getElementById('url').value;
            const result = document.getElementById('result');
            result.style.display = 'block';
            result.textContent = 'Loading...';
            fetch('/preview.php', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'url=' + encodeURIComponent(url)
            })
            .then(r => r.json())
            .then(data => {
                result.textContent = JSON.stringify(data, null, 2);
            })
            .catch(err => {
                result.textContent = 'Error: ' + err.message;
            });
        });
    </script>
</body>
</html>
