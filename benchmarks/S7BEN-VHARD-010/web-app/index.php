<?php
session_start();

// Initialize session counter
if (!isset($_SESSION['visits'])) {
    $_SESSION['visits'] = 0;
}
$_SESSION['visits']++;

// Store user input in session (for session poisoning demo)
if (isset($_GET['name'])) {
    $_SESSION['user_name'] = $_GET['name'];
}

// VULNERABILITY: LFI via page parameter
$page = isset($_GET['page']) ? $_GET['page'] : 'home';

?>
<!DOCTYPE html>
<html>
<head>
    <title>LFI Vulnerable Web App - SBEN-LFI-01</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        .header {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            margin-bottom: 30px;
            text-align: center;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            font-size: 16px;
        }
        .warning {
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
            color: #856404;
        }
        .content {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            margin-bottom: 20px;
        }
        .nav {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .nav a {
            display: inline-block;
            padding: 10px 20px;
            margin: 5px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: all 0.3s;
        }
        .nav a:hover {
            background: #5568d3;
            transform: translateY(-2px);
        }
        .info-box {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 15px 0;
        }
        .session-info {
            background: #f1f8e9;
            border-left: 4px solid #8bc34a;
            padding: 15px;
            margin: 15px 0;
        }
        pre {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .footer {
            text-align: center;
            color: white;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔓 LFI Vulnerable Web Application</h1>
            <p class="subtitle">SBEN-LFI-01: Local File Inclusion to RCE Chain</p>
        </div>

        <div class="content">
            <div class="warning">
                <strong>⚠️ Security Warning</strong><br>
                This application contains intentional LFI vulnerabilities for educational purposes.
                DO NOT deploy in production environments.
            </div>

            <div class="nav">
                <strong>Navigation:</strong>
                <a href="?page=home">Home</a>
                <a href="?page=about">About</a>
                <a href="?page=docs">Documentation</a>
                <a href="?page=contact">Contact</a>
            </div>

            <div class="session-info">
                <strong>Session Information:</strong><br>
                Session ID: <?php echo session_id(); ?><br>
                Visits: <?php echo $_SESSION['visits']; ?><br>
                <?php if (isset($_SESSION['user_name'])): ?>
                Welcome: <?php echo htmlspecialchars($_SESSION['user_name']); ?>
                <?php endif; ?>
            </div>

            <div style="background: white; padding: 20px; border-radius: 10px;">
                <?php
                // UNSAFE: Direct file inclusion with user input
                // This allows path traversal attacks
                $file_to_include = "pages/" . $page . ".php";

                // Check if file exists before including
                if (file_exists($file_to_include)) {
                    include($file_to_include);
                } else {
                    // Attempt to include anyway (VULNERABILITY)
                    @include($page);

                    if (!headers_sent()) {
                        echo "<div class='info-box'>";
                        echo "<strong>Page Not Found</strong><br>";
                        echo "The requested page could not be loaded.<br>";
                        echo "Requested: " . htmlspecialchars($page);
                        echo "</div>";
                    }
                }
                ?>
            </div>

            <div class="info-box">
                <strong>💡 Hint:</strong> Try exploring different pages using the ?page parameter.
                This application demonstrates Local File Inclusion vulnerabilities.
            </div>
        </div>

        <div class="footer">
            Strike7 Security Benchmarks | SBEN-LFI-01<br>
            Local File Inclusion Demonstration
        </div>
    </div>
</body>
</html>
