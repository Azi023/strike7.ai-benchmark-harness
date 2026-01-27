<?php
header('Content-Type: application/json');

echo json_encode([
    'status' => 'healthy',
    'service' => 'LFI Web App',
    'vulnerabilities' => ['LFI', 'Path Traversal', 'Log Poisoning', 'Session Poisoning']
]);
?>
