<h2>About This Application</h2>

<p>This is a deliberately vulnerable web application created for educational purposes as part of the Strike7 Security Benchmarks project.</p>

<h3>Vulnerabilities Included:</h3>
<ul>
    <li>CWE-98: Improper Control of Filename for Include/Require Statement</li>
    <li>CWE-22: Path Traversal</li>
    <li>Log File Poisoning</li>
    <li>Session File Poisoning</li>
</ul>

<h3>Architecture:</h3>
<pre>
web-app (172.28.0.10:80)     - Main vulnerable application
file-server (172.28.0.20:80) - Internal file repository
log-server (172.28.0.30:80)  - Logging service
</pre>

<div class="info-box">
    <strong>Internal Services:</strong><br>
    There's an internal file server at http://file-server/ that contains sensitive documents.
    Can you access it through the LFI vulnerability?
</div>
