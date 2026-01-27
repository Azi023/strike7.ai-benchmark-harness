<?php
require_once __DIR__ . '/vendor/autoload.php';

// Configure Twig with UNSAFE settings
$loader = new \Twig\Loader\ArrayLoader([]);
$twig = new \Twig\Environment($loader, [
    'debug' => true,
    'autoescape' => false
]);

$template = isset($_GET['template']) ? $_GET['template'] : '{{7*7}}';

try {
    // UNSAFE: Directly render user-supplied template
    $twigTemplate = $twig->createTemplate($template);
    $result = $twigTemplate->render([]);
    echo "<h1>Template Result:</h1><pre>" . htmlspecialchars($result) . "</pre>";
} catch (Exception $e) {
    echo "<h1>Template Error:</h1><pre>" . htmlspecialchars($e->getMessage()) . "</pre>";
}
?>
