<?php
/**
 * Patch mode management
 */

function isPatchMode() {
    $statusFile = '/tmp/patch_status.json';
    if (!file_exists($statusFile)) {
        return false;
    }
    $data = json_decode(file_get_contents($statusFile), true);
    return isset($data['patched']) && $data['patched'] === true;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && $_SERVER['REQUEST_URI'] === '/api/patch-status') {
    header('Content-Type: application/json');
    $input = json_decode(file_get_contents('php://input'), true);
    $statusFile = '/tmp/patch_status.json';

    if (isset($input['patched'])) {
        $status = ['patched' => (bool)$input['patched']];
        file_put_contents($statusFile, json_encode($status));
        echo json_encode(['status' => 'ok', 'patched' => $status['patched']]);
    } else {
        $data = json_decode(file_get_contents($statusFile), true);
        echo json_encode(['patched' => $data['patched'] ?? false]);
    }
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'GET' && $_SERVER['REQUEST_URI'] === '/api/patch-status') {
    header('Content-Type: application/json');
    $statusFile = '/tmp/patch_status.json';
    $data = json_decode(file_get_contents($statusFile), true);
    echo json_encode(['patched' => $data['patched'] ?? false]);
    exit;
}
