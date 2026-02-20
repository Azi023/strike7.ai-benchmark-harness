<?php
require_once __DIR__ . '/vendor/autoload.php';

// Configure Twig with UNSAFE settings
$loader = new \Twig\Loader\ArrayLoader([]);
$twig = new \Twig\Environment($loader, [
    'debug' => true,
    'autoescape' => false
]);

$name = isset($_GET['name']) ? $_GET['name'] : '';

if (empty($name)) {
    echo '<h1>Please enter a name!</h1><a href="/">Go back</a>';
    exit;
}

$template = "Hello, " . $name . "!";

try {
    // UNSAFE: createTemplate on user-controlled content
    $twigTemplate = $twig->createTemplate($template);
    $output = $twigTemplate->render([]);
} catch (Exception $e) {
    $output = "Error: " . htmlspecialchars($e->getMessage());
}
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
            color: #00f2fe;
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
        <h1>PHP/Twig Template Engine</h1>
        <div class="result">
            <h2>Greeting Result:</h2>
            <p><?php echo $output; ?></p>
        </div>
        <a href="/">← Back to Home</a>
    </div>
</body>
</html>
