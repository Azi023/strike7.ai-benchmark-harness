<h2>Contact Information</h2>

<p>This is a demonstration application for security training purposes.</p>

<h3>Set Your Name:</h3>
<form method="GET" action="index.php">
    <input type="hidden" name="page" value="contact">
    <input type="text" name="name" placeholder="Enter your name" style="padding: 10px; width: 300px; margin-right: 10px;">
    <button type="submit" style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">Save</button>
</form>

<?php if (isset($_SESSION['user_name'])): ?>
<div class="session-info" style="margin-top: 20px;">
    <strong>Your saved name:</strong> <?php echo htmlspecialchars($_SESSION['user_name']); ?>
</div>
<?php endif; ?>

<div class="info-box" style="margin-top: 20px;">
    <strong>💡 Session Poisoning Hint:</strong><br>
    Your input is being stored in the session. Session files are located at:<br>
    <code>/var/lib/php/sessions/sess_<?php echo session_id(); ?></code>
</div>

<h3>Project Information:</h3>
<ul>
    <li><strong>Project:</strong> Strike7 Security Benchmarks</li>
    <li><strong>Benchmark:</strong> SBEN-LFI-01</li>
    <li><strong>Category:</strong> Web Application Security</li>
    <li><strong>Difficulty:</strong> Intermediate</li>
</ul>
