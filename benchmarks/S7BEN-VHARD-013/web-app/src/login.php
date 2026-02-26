<?php
require_once __DIR__ . '/patch.php';
session_start();

$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';

    if ($username === 'demo' && $password === 'demo2026') {
        $_SESSION['authenticated'] = true;
        $_SESSION['username'] = $username;
        $_SESSION['login_time'] = time();
        header('Location: /dashboard.php');
        exit;
    } else {
        $error = 'Invalid credentials';
    }
}

if (isset($_SESSION['authenticated']) && $_SESSION['authenticated'] === true) {
    header('Location: /dashboard.php');
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign In - ContentHub</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f1117;
            color: #e4e4e7;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .card {
            background: #18181b;
            border: 1px solid #27272a;
            border-radius: 12px;
            padding: 2rem;
            width: 360px;
        }
        h1 {
            font-size: 1.5rem;
            margin-bottom: 0.25rem;
        }
        .sub { color: #71717a; font-size: 0.9rem; margin-bottom: 1.5rem; }
        label { display: block; font-size: 0.85rem; color: #a1a1aa; margin-bottom: 0.25rem; }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 0.6rem 0.75rem;
            background: #27272a;
            border: 1px solid #3f3f46;
            border-radius: 6px;
            color: #e4e4e7;
            font-size: 0.95rem;
            margin-bottom: 1rem;
        }
        input:focus { outline: none; border-color: #6366f1; }
        .btn {
            width: 100%;
            padding: 0.7rem;
            background: #6366f1;
            color: #fff;
            border: none;
            border-radius: 6px;
            font-size: 0.95rem;
            font-weight: 500;
            cursor: pointer;
        }
        .btn:hover { background: #4f46e5; }
        .error { color: #ef4444; font-size: 0.85rem; margin-bottom: 1rem; }
        .back { display: block; text-align: center; margin-top: 1rem; color: #6366f1; text-decoration: none; font-size: 0.85rem; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Sign In</h1>
        <p class="sub">Access your ContentHub account</p>
        <?php if ($error): ?>
            <p class="error"><?= htmlspecialchars($error) ?></p>
        <?php endif; ?>
        <form method="POST" action="/login.php">
            <label for="username">Username</label>
            <input type="text" id="username" name="username" required>
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required>
            <button type="submit" class="btn">Sign In</button>
        </form>
        <a href="/" class="back">Back to home</a>
    </div>
</body>
</html>
