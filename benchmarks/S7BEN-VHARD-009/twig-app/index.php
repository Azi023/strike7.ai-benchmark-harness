<?php
require_once __DIR__ . '/vendor/autoload.php';

// Flag file location
$flagFile = '/var/www/html/flag.txt';

// Create flag file if it doesn't exist
if (!file_exists($flagFile)) {
    $flagContent = getenv('FLAG_TWIG') ?: 'SBEN{twig_ssti_php_rce_i9j0k1l2}';
    file_put_contents($flagFile, $flagContent);
}

// Configure Twig with UNSAFE settings
$loader = new \Twig\Loader\ArrayLoader([]);
$twig = new \Twig\Environment($loader, [
    'debug' => true,
    'autoescape' => false
]);

// Enable string template loading (required for SSTI)
$twig->addExtension(new \Twig\Extension\StringLoaderExtension());

// Home page
if ($_SERVER['REQUEST_URI'] === '/' || $_SERVER['REQUEST_URI'] === '/index.php') {
    ?>
<!DOCTYPE html>
<html>
<head>
    <title>Twig Template Engine</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
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
        .warning {
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            color: #856404;
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
            background: #00f2fe;
            color: #333;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover {
            background: #00d9e8;
            transform: translateY(-2px);
        }
        .footer {
            text-align: center;
            margin-top: 20px;
            color: #666;
            font-size: 14px;
        }
        .hint {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            padding: 12px;
            border-radius: 8px;
            margin-top: 15px;
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

        <form method="GET" action="greet.php">
            <input type="text" name="name" placeholder="Enter your name" required>
            <button type="submit">Generate Greeting</button>
        </form>

        <div class="footer">
            GreetingCard Generator | Powered by template engine
        </div>
    </div>
</body>
</html>
    <?php
    exit;
}
?>
