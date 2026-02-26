<?php
require_once __DIR__ . '/patch.php';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Reference - ContentHub</title>
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
        .navbar .brand { font-weight: 600; color: #6366f1; font-size: 1.1rem; text-decoration: none; }
        .main { max-width: 800px; margin: 2rem auto; padding: 0 1.5rem; }
        h1 { font-size: 1.75rem; margin-bottom: 0.5rem; }
        .lead { color: #71717a; margin-bottom: 2rem; }
        .section { margin-bottom: 2rem; }
        h2 { font-size: 1.2rem; margin-bottom: 0.75rem; color: #a78bfa; }
        h3 { font-size: 1rem; margin-bottom: 0.5rem; color: #c4b5fd; }
        .card {
            background: #18181b;
            border: 1px solid #27272a;
            border-radius: 10px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }
        code {
            background: #27272a;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            font-size: 0.85rem;
            color: #c4b5fd;
        }
        pre {
            background: #09090b;
            border: 1px solid #27272a;
            border-radius: 6px;
            padding: 1rem;
            overflow-x: auto;
            font-size: 0.8rem;
            color: #a1a1aa;
            margin: 0.5rem 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 0.5rem 0;
        }
        th, td {
            text-align: left;
            padding: 0.5rem 0.75rem;
            border-bottom: 1px solid #27272a;
            font-size: 0.85rem;
        }
        th { color: #a1a1aa; }
        .tag {
            display: inline-block;
            background: #27272a;
            color: #a78bfa;
            padding: 0.1rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
            margin-right: 0.25rem;
        }
        .tag-post { background: #1e3a2f; color: #34d399; }
        .tag-get { background: #1e293b; color: #60a5fa; }
        p { color: #a1a1aa; font-size: 0.9rem; line-height: 1.6; margin-bottom: 0.5rem; }
        .back { display: block; text-align: center; margin-top: 2rem; color: #6366f1; text-decoration: none; font-size: 0.85rem; }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/" class="brand">ContentHub</a>
    </div>
    <div class="main">
        <h1>API Reference</h1>
        <p class="lead">ContentHub Platform developer documentation and SDK reference.</p>

        <div class="section">
            <h2>Authentication</h2>
            <div class="card">
                <p>The platform uses session-based authentication. Use the demo account for development and testing:</p>
                <table>
                    <tr><th>Field</th><th>Value</th></tr>
                    <tr><td>Username</td><td><code>demo</code></td></tr>
                    <tr><td>Password</td><td><code>demo2026</code></td></tr>
                </table>
            </div>
        </div>

        <div class="section">
            <h2>Endpoints</h2>

            <div class="card">
                <h3><span class="tag tag-post">POST</span> /login.php</h3>
                <p>Authenticate with username and password. Sets a session cookie on success.</p>
                <table>
                    <tr><th>Parameter</th><th>Type</th><th>Description</th></tr>
                    <tr><td><code>username</code></td><td>string</td><td>Account username</td></tr>
                    <tr><td><code>password</code></td><td>string</td><td>Account password</td></tr>
                </table>
            </div>

            <div class="card">
                <h3><span class="tag tag-get">GET</span> /dashboard.php</h3>
                <p>Main content management interface. Requires authentication.</p>
            </div>

            <div class="card">
                <h3><span class="tag tag-post">POST</span> /preview.php</h3>
                <p>Fetch and preview external content. Supports URL-based content retrieval for link previews. Requires authentication.</p>
                <table>
                    <tr><th>Parameter</th><th>Type</th><th>Description</th></tr>
                    <tr><td><code>url</code></td><td>string</td><td>URL to fetch and preview</td></tr>
                </table>
                <pre>{
  "url": "https://example.com",
  "status": 200,
  "content": "&lt;html&gt;...&lt;/html&gt;",
  "content_length": 1256
}</pre>
            </div>

            <div class="card">
                <h3><span class="tag tag-get">GET</span> /status.php</h3>
                <p>Platform status and configuration. Requires authentication. Returns system configuration as JSON.</p>
            </div>

            <div class="card">
                <h3><span class="tag tag-get">GET</span> /health.php</h3>
                <p>Health check endpoint for monitoring.</p>
            </div>
        </div>

        <div class="section">
            <h2>Platform SDK Reference</h2>
            <p>Core utility classes available for integration and extension.</p>

            <div class="card">
                <h3>CacheManager</h3>
                <p>Manages cached data with configurable storage backends and key prefixes.</p>
                <table>
                    <tr><th>Property</th><th>Type</th><th>Default</th></tr>
                    <tr><td><code>store</code></td><td>object</td><td>null</td></tr>
                    <tr><td><code>prefix</code></td><td>string</td><td>"cache_"</td></tr>
                    <tr><td><code>ttl</code></td><td>int</td><td>3600</td></tr>
                </table>
                <p>Methods: <code>get($key)</code>, <code>set($key, $value)</code></p>
            </div>

            <div class="card">
                <h3>FileStore</h3>
                <p>File-based storage backend for persistent data management.</p>
                <table>
                    <tr><th>Property</th><th>Type</th><th>Default</th></tr>
                    <tr><td><code>basePath</code></td><td>string</td><td>/tmp/store</td></tr>
                    <tr><td><code>extension</code></td><td>string</td><td>.dat</td></tr>
                </table>
                <p>Methods: <code>get($key)</code>, <code>put($key, $value)</code></p>
            </div>

            <div class="card">
                <h3>Logger</h3>
                <p>Buffered logging utility with configurable output destination.</p>
                <table>
                    <tr><th>Property</th><th>Type</th><th>Default</th></tr>
                    <tr><td><code>logFile</code></td><td>string</td><td>/tmp/app.log</td></tr>
                    <tr><td><code>buffer</code></td><td>array</td><td>[]</td></tr>
                </table>
                <p>Methods: <code>log($message)</code>, <code>flush()</code></p>
            </div>

            <div class="card">
                <h3>Config</h3>
                <p>Key-value configuration container with JSON export support.</p>
                <table>
                    <tr><th>Property</th><th>Type</th><th>Default</th></tr>
                    <tr><td><code>data</code></td><td>array</td><td>[]</td></tr>
                </table>
                <p>Methods: <code>get($key, $default)</code>, <code>set($key, $value)</code>, <code>all()</code></p>
            </div>
        </div>

        <a href="/" class="back">Back to home</a>
    </div>
</body>
</html>
