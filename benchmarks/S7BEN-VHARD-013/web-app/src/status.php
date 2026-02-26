<?php
require_once __DIR__ . '/patch.php';
session_start();

header('Content-Type: application/json');

if (!isset($_SESSION['authenticated']) || $_SESSION['authenticated'] !== true) {
    http_response_code(401);
    echo json_encode(['error' => 'Authentication required']);
    exit;
}

echo json_encode([
    'platform' => 'ContentHub',
    'version' => '3.2.1',
    'session' => [
        'handler' => 'redis',
        'connection' => 'tcp://redis:6379',
        'prefix' => 'PHPREDIS_SESSION:'
    ],
    'features' => [
        'preview' => true,
        'cache' => true,
        'logging' => true
    ]
], JSON_PRETTY_PRINT);
