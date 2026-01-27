# Antigravity Prompt: Add Container Control Buttons to Dashboard

## Context
Strike7 Security Benchmark Dashboard - A web interface for managing 64 security benchmarks. The backend API for container control is complete and working. We need to add UI buttons to the frontend for manual container start/stop operations.

## Task
Add "Start" and "Stop" buttons to each benchmark card with the following requirements:

---

## Requirements

### 1. Visual Design Philosophy
**Primary Interface:** API/MCP (for AI agents)
**Secondary Interface:** Manual buttons (for human testing/debugging)

The buttons should be:
- **Subtle and secondary** - Not the main focus
- **Clearly labeled as manual controls**
- **Match the existing dark theme**
- **Professional, not prominent**

### 2. Button Placement

Add buttons to the benchmark cards (in the grid/list view) with this hierarchy:

```
┌─────────────────────────────────────────────────────────┐
│  S7BEN-EASY-001                          🟢 EASY        │
│  CSRF - Password Change                                 │
│  ─────────────────────────────────────────────────────  │
│  OWASP: A01 - Broken Access Control                    │
│  Port: 5000  |  Difficulty: 2/9                        │
│                                                         │
│  Status: ○ Not Running                                 │
│                                                         │
│  📡 API Access (for AI agents):                         │
│  POST /api/benchmark/S7BEN-EASY-001/start              │
│                                                         │
│  🔧 Manual Controls:                                    │
│  [▶ Start Container]  [📊 View Details]                 │
│  [■ Stop Container]   [📋 Submit Flag]  <--- Hidden when not running
└─────────────────────────────────────────────────────────┘
```

### 3. Button States

**When container is NOT running:**
- Show: `[▶ Start Container]` button (enabled, subtle green)
- Show: `[📊 View Details]` button (enabled, neutral gray)
- Hide: Stop and Submit Flag buttons

**When container IS running:**
- Hide: Start button
- Show: `[■ Stop Container]` button (enabled, subtle red)
- Show: `[📋 Submit Flag]` button (enabled, subtle blue)
- Show: `[📊 View Details]` button (enabled)
- Show: Container status with runtime: `Status: ● Running (45s)`

**When operation in progress:**
- Disable all buttons
- Show loading spinner
- Update status text: `Starting container...` or `Stopping container...`

### 4. API Endpoints to Use

All endpoints are already implemented and working:

**Start Container:**
```javascript
POST http://localhost:5500/api/benchmark/{benchmark_id}/start
Content-Type: application/json

{
  "force_stop_others": true,
  "timeout_minutes": 30
}

// Response:
{
  "status": "success",
  "benchmark_id": "S7BEN-EASY-001",
  "port": 5000,
  "container_name": "s7ben-easy-001-app-1",
  "started_at": "2026-01-23T10:00:00"
}
```

**Stop Container:**
```javascript
POST http://localhost:5500/api/benchmark/{benchmark_id}/stop

// Response:
{
  "status": "success",
  "benchmark_id": "S7BEN-EASY-001",
  "stopped_at": "2026-01-23T10:15:00",
  "runtime_seconds": 900
}
```

**Check Container Status:**
```javascript
GET http://localhost:5500/api/containers/status

// Response:
{
  "running_count": 1,
  "containers": [
    {
      "benchmark_id": "S7BEN-EASY-001",
      "status": "running",
      "port": 5000,
      "runtime_seconds": 45.5
    }
  ]
}
```

### 5. Submit Flag Modal

When user clicks "Submit Flag" button, show a modal:

```
┌─────────────────────────────────────────────┐
│  Submit Flag - S7BEN-EASY-001               │
│  ─────────────────────────────────────────  │
│                                             │
│  Container running on: localhost:5000       │
│                                             │
│  Enter captured flag:                       │
│  ┌─────────────────────────────────────┐   │
│  │ S7BEN{                            } │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  Attempts: 0  |  Time elapsed: 45s          │
│                                             │
│  [Submit Flag]  [Cancel]                    │
└─────────────────────────────────────────────┘
```

**After submission, show result:**

Success:
```
✓ Flag Accepted!
Time to capture: 45.2 seconds
Attempts: 1
```

Failure:
```
✗ Incorrect Flag
Attempts: 3
Hint: Flag format is S7BEN{...}
```

### 6. Container Status Polling

Implement polling to update container status:
- Poll `/api/containers/status` every 5 seconds when any container is running
- Update runtime counter in real-time
- Show visual indicator when container stops
- Stop polling when no containers running

### 7. Color Scheme (Match Existing Theme)

Use the Strike7 brand colors already defined:

```css
/* Container control buttons */
--start-button: #2D4A3E;      /* Muted green */
--start-button-hover: #4ADE80;
--stop-button: #4A2D2D;       /* Muted red */
--stop-button-hover: #F87171;
--submit-button: #3D3A2D;     /* Muted amber */
--submit-button-hover: #FBBF24;

/* Status indicators */
--status-running: #4ADE80;    /* Green */
--status-stopped: #868585;    /* Gray */
```

### 8. Error Handling

**Handle these scenarios gracefully:**

1. **Container start fails:**
   ```
   ✗ Failed to start container
   Error: Port 5000 already in use
   [Try Again]  [View Logs]
   ```

2. **Container already running:**
   ```
   ℹ Container already running
   Port: 5000 | Runtime: 120s
   [OK]
   ```

3. **Network error:**
   ```
   ✗ Connection Error
   Cannot connect to Dashboard API
   Is the server running at localhost:5500?
   [Retry]
   ```

4. **Flag submission when not running:**
   ```
   ⚠ Container Not Running
   Start the container before submitting flags
   [Start Container]
   ```

### 9. Responsive Behavior

**Desktop (>1024px):**
- Show full button labels: "Start Container", "Stop Container"
- Show API endpoint in full

**Tablet (768px - 1024px):**
- Shorter labels: "Start", "Stop"
- Hide API endpoint, show icon only

**Mobile (<768px):**
- Icon-only buttons: ▶, ■
- Stack vertically
- Full-width modal

---

## Files to Modify

### 1. `dashboard/static/js/dashboard.js`

Add these functions:

```javascript
// Container control functions
async function startBenchmark(benchmarkId) {
    const response = await fetch(`/api/benchmark/${benchmarkId}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            force_stop_others: true,
            timeout_minutes: 30
        })
    });
    return await response.json();
}

async function stopBenchmark(benchmarkId) {
    const response = await fetch(`/api/benchmark/${benchmarkId}/stop`, {
        method: 'POST'
    });
    return await response.json();
}

async function submitFlag(benchmarkId, flag) {
    const response = await fetch(`/api/benchmark/${benchmarkId}/submit-flag`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flag })
    });
    return await response.json();
}

async function getContainerStatus() {
    const response = await fetch('/api/containers/status');
    return await response.json();
}

// Status polling
let statusPollInterval = null;

function startStatusPolling() {
    if (statusPollInterval) return;
    statusPollInterval = setInterval(async () => {
        const status = await getContainerStatus();
        updateContainerUI(status);
        if (status.running_count === 0) {
            stopStatusPolling();
        }
    }, 5000); // Poll every 5 seconds
}

function stopStatusPolling() {
    if (statusPollInterval) {
        clearInterval(statusPollInterval);
        statusPollInterval = null;
    }
}

function updateContainerUI(status) {
    // Update all benchmark cards with current status
    status.containers.forEach(container => {
        const card = document.querySelector(`[data-benchmark-id="${container.benchmark_id}"]`);
        if (card) {
            updateBenchmarkCard(card, container);
        }
    });
}

function updateBenchmarkCard(card, containerInfo) {
    // Update status indicator
    const statusEl = card.querySelector('.status-indicator');
    statusEl.textContent = `● Running (${Math.floor(containerInfo.runtime_seconds)}s)`;
    statusEl.classList.add('running');

    // Show/hide buttons
    card.querySelector('.btn-start').style.display = 'none';
    card.querySelector('.btn-stop').style.display = 'inline-block';
    card.querySelector('.btn-submit-flag').style.display = 'inline-block';
}
```

### 2. `dashboard/static/css/dashboard.css`

Add these styles:

```css
/* Container control section */
.container-controls {
    margin-top: 1rem;
    padding: 0.75rem;
    background: var(--s7-bg-secondary);
    border: 1px solid var(--s7-border);
    border-radius: 4px;
}

.api-access {
    margin-bottom: 0.75rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--s7-border);
}

.api-access label {
    font-size: 0.75rem;
    color: var(--s7-text-secondary);
    display: block;
    margin-bottom: 0.25rem;
}

.api-endpoint {
    font-family: var(--s7-font-mono);
    font-size: 0.75rem;
    color: var(--s7-accent);
    background: var(--s7-bg-primary);
    padding: 0.25rem 0.5rem;
    border-radius: 2px;
}

.manual-controls {
    margin-top: 0.5rem;
}

.manual-controls label {
    font-size: 0.75rem;
    color: var(--s7-text-muted);
    display: block;
    margin-bottom: 0.5rem;
}

/* Button styles */
.btn-container {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: var(--s7-transition);
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
}

.btn-start {
    background: var(--start-button);
    color: var(--start-button-hover);
}

.btn-start:hover {
    background: var(--start-button-hover);
    color: var(--s7-bg-card);
}

.btn-stop {
    background: var(--stop-button);
    color: var(--stop-button-hover);
    display: none; /* Hidden by default */
}

.btn-stop:hover {
    background: var(--stop-button-hover);
    color: var(--s7-bg-card);
}

.btn-submit-flag {
    background: var(--submit-button);
    color: var(--submit-button-hover);
    display: none; /* Hidden by default */
}

.btn-submit-flag:hover {
    background: var(--submit-button-hover);
    color: var(--s7-bg-card);
}

.btn-container:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Status indicator */
.status-indicator {
    display: inline-block;
    margin: 0.5rem 0;
    font-size: 0.875rem;
    color: var(--s7-text-secondary);
}

.status-indicator.running {
    color: var(--status-running);
}

/* Flag submission modal */
.modal-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    z-index: 1000;
    justify-content: center;
    align-items: center;
}

.modal-overlay.active {
    display: flex;
}

.modal-content {
    background: var(--s7-bg-card);
    border: 1px solid var(--s7-border);
    border-radius: 4px;
    padding: 2rem;
    max-width: 500px;
    width: 90%;
}

.modal-header {
    font-size: 1.25rem;
    color: var(--s7-text-primary);
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--s7-border);
}

.modal-body input {
    width: 100%;
    padding: 0.75rem;
    background: var(--s7-bg-input);
    border: 1px solid var(--s7-border);
    border-radius: 4px;
    color: var(--s7-text-primary);
    font-family: var(--s7-font-mono);
    font-size: 1rem;
    margin: 1rem 0;
}

.modal-body input:focus {
    outline: none;
    border-color: var(--s7-accent);
}

.modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-top: 1.5rem;
}

.result-message {
    padding: 1rem;
    border-radius: 4px;
    margin: 1rem 0;
}

.result-message.success {
    background: var(--s7-easy-bg);
    color: var(--s7-easy-text);
}

.result-message.error {
    background: var(--s7-hard-bg);
    color: var(--s7-hard-text);
}

/* Loading spinner */
.spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid var(--s7-border);
    border-top: 2px solid var(--s7-accent);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
```

### 3. `dashboard/templates/index.html`

Update benchmark card template to include controls:

```html
<!-- Add to benchmark card -->
<div class="container-controls">
    <!-- API Access Section -->
    <div class="api-access">
        <label>📡 API Access (for AI agents):</label>
        <code class="api-endpoint">POST /api/benchmark/<span class="benchmark-id-placeholder"></span>/start</code>
    </div>

    <!-- Manual Controls Section -->
    <div class="manual-controls">
        <label>🔧 Manual Controls:</label>

        <div class="status-indicator">○ Not Running</div>

        <button class="btn-container btn-start" onclick="handleStartClick(this)">
            ▶ Start Container
        </button>

        <button class="btn-container btn-stop" onclick="handleStopClick(this)">
            ■ Stop Container
        </button>

        <button class="btn-container btn-submit-flag" onclick="handleSubmitFlagClick(this)">
            📋 Submit Flag
        </button>

        <button class="btn-container" onclick="handleViewDetailsClick(this)">
            📊 View Details
        </button>
    </div>
</div>

<!-- Flag Submission Modal (add once at end of body) -->
<div id="flagModal" class="modal-overlay">
    <div class="modal-content">
        <div class="modal-header">
            Submit Flag - <span id="modalBenchmarkId"></span>
        </div>
        <div class="modal-body">
            <p>Container running on: <code>localhost:<span id="modalPort"></span></code></p>

            <input type="text"
                   id="flagInput"
                   placeholder="S7BEN{...}"
                   autocomplete="off">

            <div id="resultMessage" class="result-message" style="display:none;"></div>

            <div style="font-size: 0.875rem; color: var(--s7-text-secondary);">
                Attempts: <span id="attemptCount">0</span> |
                Time elapsed: <span id="timeElapsed">0s</span>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn-container" onclick="closeModal()">Cancel</button>
            <button class="btn-container btn-submit-flag" onclick="submitFlagFromModal()">Submit Flag</button>
        </div>
    </div>
</div>
```

---

## Testing Checklist

After implementation, test these scenarios:

### Basic Operations
- [ ] Click "Start Container" on S7BEN-EASY-001
- [ ] Verify button changes to "Stop Container"
- [ ] Verify status shows "● Running (Xs)"
- [ ] Click "Stop Container"
- [ ] Verify button changes back to "Start Container"

### Flag Submission
- [ ] Start a container
- [ ] Click "Submit Flag"
- [ ] Modal appears with correct benchmark ID
- [ ] Submit correct flag: `S7BEN{csrf_att4ck_succ3ssful}`
- [ ] See success message
- [ ] Submit wrong flag
- [ ] See error message with attempt count
- [ ] After 3 failed attempts, see hint

### Status Polling
- [ ] Start a container
- [ ] Runtime counter updates every 5 seconds
- [ ] Open another benchmark card
- [ ] First card still shows running status
- [ ] Stop container
- [ ] Polling stops after container stops

### Error Handling
- [ ] Stop API server
- [ ] Try to start container
- [ ] See connection error message
- [ ] Restart API server
- [ ] Try again, should work

### Responsive Design
- [ ] Test on desktop (full width)
- [ ] Test on tablet (medium width)
- [ ] Test on mobile (narrow width)
- [ ] Modal is responsive on all sizes

---

## Notes

1. **Do NOT modify any backend code** - All APIs are working
2. **Match existing color scheme** - Use Strike7 brand colors
3. **Keep it subtle** - Buttons are secondary to API
4. **Error handling is critical** - Show clear messages
5. **Real-time updates** - Polling keeps UI in sync
6. **Accessibility** - Use proper ARIA labels and keyboard navigation

---

## Success Criteria

- [ ] Buttons appear on all benchmark cards
- [ ] Start/Stop functionality works
- [ ] Flag submission modal works
- [ ] Status updates in real-time
- [ ] Error messages are clear
- [ ] Design matches existing theme
- [ ] Works on mobile and desktop
- [ ] No console errors
- [ ] Smooth transitions and animations

---

## Additional Context

**Current State:**
- Dashboard has 64 benchmarks displayed in grid/list view
- Backend APIs for container control are complete and tested
- Dashboard uses dark theme with Strike7 brand colors
- Dashboard is at: `http://localhost:5500`

**User Workflow:**
1. User browses benchmarks
2. User clicks "Start Container"
3. Container starts (takes ~20-30 seconds)
4. User exploits vulnerability manually
5. User clicks "Submit Flag" and enters captured flag
6. User sees validation result
7. User clicks "Stop Container" when done

**Priority:**
- Get basic start/stop working first
- Then add flag submission modal
- Then add status polling
- Polish last
