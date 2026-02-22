<h2>Welcome to the LFI Demo Application</h2>

<p>This application demonstrates Local File Inclusion (LFI) vulnerabilities and various exploitation techniques.</p>

<h3>What is LFI?</h3>
<p>Local File Inclusion (LFI) is a vulnerability that allows an attacker to include files from the local file system through the web application. This can lead to:</p>

<ul>
    <li>Sensitive file disclosure</li>
    <li>Source code exposure</li>
    <li>Configuration file access</li>
    <li>Remote Code Execution (via log poisoning, session poisoning, etc.)</li>
</ul>

<h3>Attack Vectors</h3>
<ol>
    <li><strong>Path Traversal</strong>: Using ../ sequences to access files outside the intended directory</li>
    <li><strong>PHP Wrappers</strong>: Using php://filter, php://input for advanced exploitation</li>
    <li><strong>Log Poisoning</strong>: Injecting PHP code into log files and including them</li>
    <li><strong>Session Poisoning</strong>: Injecting PHP code into session data</li>
</ol>

