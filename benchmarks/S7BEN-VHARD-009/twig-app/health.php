<?php
header('Content-Type: application/json');

echo json_encode([
    'status' => 'healthy',
    'engine' => 'default',
    'language' => 'PHP'
]);
?>
