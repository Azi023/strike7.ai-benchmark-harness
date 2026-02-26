<?php
header('Content-Type: application/json');
echo json_encode(['status' => 'healthy', 'service' => 'contenthub-web']);
