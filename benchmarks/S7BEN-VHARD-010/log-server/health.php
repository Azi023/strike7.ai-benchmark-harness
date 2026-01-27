<?php
header('Content-Type: application/json');

echo json_encode([
    'status' => 'healthy',
    'service' => 'Log Server',
    'log_file' => '/var/log/apache2/access.log'
]);
?>
