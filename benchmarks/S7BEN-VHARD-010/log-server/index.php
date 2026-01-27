<?php
// Simple logging service that demonstrates log poisoning
?>
<!DOCTYPE html>
<html>
<head>
    <title>Log Server - SBEN-LFI-01</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #2c3e50;
            color: white;
        }
        .header {
            background: #34495e;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .log-container {
            background: #1a1a1a;
            padding: 20px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            overflow-x: auto;
        }
        .flag-box {
            background: #27ae60;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            text-align: center;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🗂️ Apache Log Server</h1>
        <p>Centralized logging service for all applications</p>
    </div>

    <div class="log-container">
        <h3>Recent Access Logs:</h3>
        <pre><?php
        $logFile = '/var/log/apache2/access.log';
        if (file_exists($logFile)) {
            $logs = file_get_contents($logFile);
            echo htmlspecialchars(substr($logs, -2000)); // Last 2000 chars
        } else {
            echo "Log file not found or empty.";
        }
        ?></pre>
    </div>

    <div class="flag-box">
        🚩 Log Poisoning Flag: <?php echo getenv('FLAG_LOG') ?: 'SBEN{apache_log_poisoning_rce_d4e5f6}'; ?>
    </div>

    <div style="background: #34495e; padding: 15px; border-radius: 5px; margin-top: 20px;">
        <strong>Hint:</strong> Apache logs are stored at /var/log/apache2/access.log<br>
        Try poisoning the User-Agent header with PHP code and then include the log file!
    </div>
</body>
</html>
