// Strike7 Dashboard JavaScript - SOC Theme

const API_BASE = 'http://localhost:5500/api';

// SOC Color Palette
const COLORS = {
    primary: '#E63F2B',
    accent: '#E63F2B',
    success: '#4ADE80',
    warning: '#FBBF24',
    danger: '#F87171',
    info: '#818CF8',
    text: '#FAFAFA',
    textSecondary: '#ACACAC',
    grid: '#252525'
};

const CATEGORY_COLORS = {
    'EASY': '#4ADE80',
    'MED': '#FBBF24',
    'HARD': '#F87171',
    'VHARD': '#A78BFA',
    'CVE': '#E63F2B'
};

let allBenchmarks = [];
let filteredBenchmarks = [];
let statistics = {};
let activeCharts = {};
let statusPollInterval = null;
let currentModalBenchmark = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    await loadBenchmarks();
    await loadStatistics();
    initializeEventListeners();
    initializeCharts();

    // Start initial polling to see if any containers are already running
    startStatusPolling();
});

// Load all benchmarks
async function loadBenchmarks() {
    try {
        const response = await fetch(`${API_BASE}/benchmarks`);
        const data = await response.json();
        allBenchmarks = data.benchmarks;
        filteredBenchmarks = allBenchmarks;

        updateTotalCount();
        displayBenchmarks();
        updateCategoryBreakdown();
    } catch (error) {
        console.error('Error loading benchmarks:', error);
        showError('Failed to load benchmarks');
    }
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE}/statistics`);
        statistics = await response.json();

        updateHeaderStats();
        displayStatistics();
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Update header statistics
function updateHeaderStats() {
    document.getElementById('total-count').textContent = statistics.total_benchmarks || 0;

    // Count OWASP categories covered
    const owaspCount = Object.keys(statistics.by_owasp || {}).length;
    document.getElementById('owasp-coverage').textContent = `${owaspCount}/10`;
}

// Update total count
function updateTotalCount() {
    const count = filteredBenchmarks.length;
    document.getElementById('results-count').textContent =
        `Showing ${count} benchmark${count !== 1 ? 's' : ''}`;
}

// Display benchmarks
function displayBenchmarks() {
    const container = document.getElementById('benchmarks-container');
    container.innerHTML = '';

    if (filteredBenchmarks.length === 0) {
        container.innerHTML = '<div class="loading">No benchmarks found matching your filters</div>';
        return;
    }

    filteredBenchmarks.forEach(benchmark => {
        const card = createBenchmarkCard(benchmark);
        container.appendChild(card);
    });
}

// Create benchmark card with controls
// Create benchmark card with controls
function createBenchmarkCard(benchmark) {
    const card = document.createElement('div');
    card.className = 'benchmark-card';
    card.dataset.benchmarkId = benchmark.id;
    // Note: Removed onclick handler to prevent triggering modal when clicking buttons

    // OWASP short code
    const owaspCode = benchmark.owasp ? benchmark.owasp.split(':')[0].trim() : 'N/A';

    // Difficulty segments (1-9)
    let segmentsHTML = '';
    const difficulty = benchmark.difficulty || 1;
    let diffClass = 'difficulty-low';
    if (difficulty > 3) diffClass = 'difficulty-med';
    if (difficulty > 6) diffClass = 'difficulty-high';

    for (let i = 1; i <= 9; i++) {
        const filled = i <= difficulty ? 'filled' : '';
        segmentsHTML += `<div class="diff-seg ${filled}"></div>`;
    }

    card.innerHTML = `
        <div class="benchmark-header">
            <span class="benchmark-id">${benchmark.id}</span>
            <span class="badge badge-${benchmark.category}">${benchmark.category}</span>
        </div>
        <div class="benchmark-name">${benchmark.name}</div>
        
        <div class="benchmark-meta">
            <div class="meta-item">
                <span class="meta-label">OWASP</span>
                <span class="meta-value">${owaspCode}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Port</span>
                <span class="meta-value">${benchmark.port}</span>
            </div>
        </div>

        <div class="difficulty-meter ${diffClass}">
            ${segmentsHTML}
        </div>

        <!-- Container Controls -->
        <div class="container-controls">
            <!-- API Access Section -->
            <div class="api-access">
                <label>📡 API Access (for AI agents):</label>
                <code class="api-endpoint">POST /api/benchmark/${benchmark.id}/start</code>
            </div>

            <!-- Manual Controls Section -->
            <div class="manual-controls">
                <label>🔧 Manual Controls:</label>
                
                <div class="status-indicator">○ Not Running</div>

                 <!-- Running Info / Access Box (Hidden by default) -->
                <div class="running-info" style="display: none;">
                    <div class="access-info-box">
                        <div class="access-header">
                            <span class="status-dot running"></span>
                            <strong>Container Running</strong>
                            <span class="runtime-counter">0s</span>
                        </div>

                        <div class="access-url-section">
                            <label>🌐 Access Benchmark:</label>
                            <div class="url-display">
                                <code class="access-url">http://localhost:<span class="port-number">${benchmark.port}</span></code>
                                <button class="btn-icon btn-copy" onclick="copyAccessUrl(this)" title="Copy URL">
                                    📋
                                </button>
                                <button class="btn-icon btn-open" onclick="openInBrowser(this)" title="Open in Browser">
                                    🔗
                                </button>
                            </div>
                        </div>

                        <div class="quick-actions">
                            <small>Quick Actions:</small>
                            <div class="action-buttons">
                                <button class="btn-container btn-stop" onclick="handleStopClick('${benchmark.id}')">
                                    ■ Stop Container
                                </button>
                                <button class="btn-container btn-submit-flag" onclick="handleSubmitFlagClick('${benchmark.id}', ${benchmark.port})">
                                    📋 Submit Flag
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="controls-actions" style="display: flex; flex-wrap: wrap;">
                    <button class="btn-container btn-start" onclick="handleStartClick('${benchmark.id}')">
                        ▶ Start
                    </button>

                    <!-- Stop/Submit buttons moved into running-info but kept here for fallback/logic consistency if needed, 
                         but spec says they are inside running-info. However, basic controls might still be needed outside? 
                         Actually spec puts them INSIDE running-info.
                         But we should keep the 'Start' button outside. 
                         Let's keep the details button here. -->

                    <button class="btn-container btn-details" onclick="showBenchmarkDetails('${benchmark.id}')">
                        📊 Details
                    </button>
                </div>
            </div>
        </div>
    `;

    return card;
}

// --- Container Control Functions ---

async function startBenchmark(benchmarkId) {
    // Note: UI updates are handled by caller or polling
    const response = await fetch(`/api/benchmark/${benchmarkId}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            force_stop_others: true,
            timeout_minutes: 30
        })
    });

    const data = await response.json();

    if (!response.ok) {
        const error = new Error(data.message || data.error || 'Failed to start container');
        error.status = response.status;
        throw error;
    }

    // Trigger immediate status update
    await getContainerStatus().then(updateContainerUI);

    // Ensure polling is active
    startStatusPolling();

    return { status: 'success', ...data };
}

async function stopBenchmark(benchmarkId) {
    // UI update handled by caller
    const response = await fetch(`/api/benchmark/${benchmarkId}/stop`, {
        method: 'POST'
    });

    const data = await response.json();

    // Trigger immediate status update
    await getContainerStatus().then(updateContainerUI);

    return data;
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

// --- Status Polling & UI Updates ---

function startStatusPolling() {
    if (statusPollInterval) return;

    // Initial call
    getContainerStatus().then(status => {
        updateContainerUI(status);
        if (status.running_count > 0) {
            // Start interval if we have running containers
            statusPollInterval = setInterval(async () => {
                const status = await getContainerStatus();
                updateContainerUI(status);
                if (status.running_count === 0) {
                    stopStatusPolling();
                }
            }, 5000); // Poll every 5 seconds
        }
    });
}

function stopStatusPolling() {
    if (statusPollInterval) {
        clearInterval(statusPollInterval);
        statusPollInterval = null;
    }
}

function updateContainerUI(status) {
    // Determine running IDs
    const runningIds = new Set(status.containers.map(c => c.benchmark_id));

    // Update header running count
    const runningCard = document.getElementById('running-card');
    const runningCountEl = document.getElementById('running-count');

    if (runningCountEl) {
        runningCountEl.textContent = status.running_count;
        if (status.running_count > 0) {
            runningCard.classList.add('running-active');
        } else {
            runningCard.classList.remove('running-active');
        }
    }

    // Process all cards
    document.querySelectorAll('.benchmark-card').forEach(card => {
        const benchmarkId = card.dataset.benchmarkId;
        const containerInfo = status.containers.find(c => c.benchmark_id === benchmarkId);
        const isRunning = runningIds.has(benchmarkId);

        updateButtonVisibility(card, isRunning);

        if (isRunning && containerInfo) {
            updateBenchmarkCardRunning(card, containerInfo);
            // Update status indicator text as well
            const statusEl = card.querySelector('.status-indicator');
            if (statusEl) statusEl.textContent = '● Running';
        } else {
            // Ensure runtime counter is stopped if not running
            const statusEl = card.querySelector('.status-indicator');
            if (statusEl) statusEl.textContent = '○ Not Running';
        }
    });

    // If we have running containers but no interval, start it
    if (status.running_count > 0 && !statusPollInterval) {
        startStatusPolling();
    }
}

function updateButtonVisibility(card, isRunning) {
    const startBtn = card.querySelector('.btn-start');
    const runningInfo = card.querySelector('.running-info');
    const statusDot = card.querySelector('.status-dot');

    // Note: Stop and Submit buttons are now inside running-info

    if (isRunning) {
        // Container is running
        startBtn.style.display = 'none';
        runningInfo.style.display = 'block';
        if (statusDot) statusDot.classList.add('running');
    } else {
        // Container is not running
        startBtn.style.display = 'inline-block';
        runningInfo.style.display = 'none';
        if (statusDot) statusDot.classList.remove('running');
    }
}

function updateBenchmarkCardRunning(card, containerInfo) {
    // Store port in card data
    card.dataset.port = containerInfo.port;
    card.dataset.benchmarkId = containerInfo.benchmark_id;

    // Show running info
    const runningInfo = card.querySelector('.running-info');
    runningInfo.style.display = 'block';

    // Update port number in display
    const portEl = card.querySelector('.port-number');
    if (portEl) portEl.textContent = containerInfo.port;

    // Update access URL if present
    const urlEl = card.querySelector('.access-url');
    if (urlEl) {
        urlEl.innerHTML = `http://localhost:<span class="port-number">${containerInfo.port}</span>`;
    }

    // Start runtime counter
    if (containerInfo.started_at) {
        startRuntimeCounter(card, containerInfo.started_at);
    }
}

function startRuntimeCounter(card, startedAt) {
    const counterEl = card.querySelector('.runtime-counter');
    if (!counterEl) return;

    // Clear existing interval if any (store in element to handle per-card)
    if (counterEl.dataset.interval) {
        clearInterval(parseInt(counterEl.dataset.interval));
    }

    const startTime = new Date(startedAt).getTime();

    // Initial update
    const update = () => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        counterEl.textContent = formatRuntime(elapsed);

        // Stop if card no longer shows running
        if (card.querySelector('.running-info').style.display === 'none') {
            if (counterEl.dataset.interval) clearInterval(parseInt(counterEl.dataset.interval));
        }
    };

    update();

    // Update every second
    const interval = setInterval(update, 1000);
    counterEl.dataset.interval = interval;
}

function formatRuntime(seconds) {
    if (seconds < 0) return '0s'; // Clock skew protection
    if (seconds < 60) {
        return `${seconds}s`;
    } else if (seconds < 3600) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}m ${secs}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${mins}m`;
    }
}

// --- Event Handlers ---

async function handleStartClick(benchmarkId) {
    const card = document.querySelector(`.benchmark-card[data-benchmark-id="${benchmarkId}"]`);
    const button = card ? card.querySelector('.btn-start') : null;

    if (button) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner"></span> Starting...';
    }

    try {
        const result = await startBenchmark(benchmarkId);

        if (result.status === 'success') {
            // Update UI handled by polling/updateContainerUI
            showNotification('success', `${benchmarkId} started successfully`);
        } else {
            showNotification('error', result.message || 'Failed to start container');
        }
    } catch (error) {
        const message = handleApiError(error, 'start');
        showNotification('error', message);
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = '▶ Start';
        }
    }
}

async function handleStopClick(benchmarkId) {
    const card = document.querySelector(`.benchmark-card[data-benchmark-id="${benchmarkId}"]`);
    const button = card ? card.querySelector('.btn-stop') : null;
    const originalText = button ? button.innerHTML : '■ Stop Container';

    if (button) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner"></span> Stopping...';
    }

    try {
        await stopBenchmark(benchmarkId);
        showNotification('success', `${benchmarkId} stopped`);
    } catch (error) {
        const message = handleApiError(error, 'stop');
        showNotification('error', message);
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }
}

function handleSubmitFlagClick(benchmarkId, port) {
    openFlagModal(benchmarkId, port);
}

// --- Modal Logic ---

// --- Modal Logic ---

function showFlagModal(benchmarkId, port) {
    const modal = document.getElementById('flagModal');
    const input = document.getElementById('flagInput');
    const modalBenchmarkId = document.getElementById('modalBenchmarkId');
    const modalPort = document.getElementById('modalPort');
    const resultMessage = document.getElementById('resultMessage');
    const attemptCount = document.getElementById('attemptCount');

    // Set modal data
    if (modalBenchmarkId) modalBenchmarkId.textContent = benchmarkId;
    if (modalPort) modalPort.textContent = port;

    // Clear previous state
    input.value = '';
    input.disabled = false;
    if (resultMessage) resultMessage.style.display = 'none';
    if (attemptCount) attemptCount.textContent = '0';

    // Store benchmark ID for submission
    modal.dataset.benchmarkId = benchmarkId;

    // Show modal
    modal.classList.add('active');

    // Focus input for immediate typing
    setTimeout(() => input.focus(), 100);

    // Allow Enter key to submit
    // Remove old listeners to prevent duplicates (cloning)
    const newInput = input.cloneNode(true);
    input.parentNode.replaceChild(newInput, input);

    newInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            submitFlagFromModal();
        }
    });
}

// Alias for click handler
const openFlagModal = showFlagModal;

function closeModal() {
    const modal = document.getElementById('flagModal');
    if (modal) modal.classList.remove('active');

    // Also close details modal
    closeDetailsModal();

    // Clear form
    const input = document.getElementById('flagInput');
    const resultMessage = document.getElementById('resultMessage');
    if (input) input.value = '';
    if (resultMessage) resultMessage.style.display = 'none';
}

function closeDetailsModal() {
    const modal = document.getElementById('detailsModal');
    if (modal) modal.classList.remove('active');
    // Also try the old ID just in case
    const oldModal = document.getElementById('benchmark-modal');
    if (oldModal) oldModal.style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function (event) {
    const flagModal = document.getElementById('flagModal');
    if (event.target == flagModal) {
        closeModal();
    }
    const detailsModal = document.getElementById('detailsModal');
    if (event.target == detailsModal) {
        closeDetailsModal();
    }
}

async function submitFlagFromModal() {
    const modal = document.getElementById('flagModal');
    const input = document.getElementById('flagInput');
    const resultMessage = document.getElementById('resultMessage');
    const submitButton = modal.querySelector('.btn-submit-flag');
    const attemptCountEl = document.getElementById('attemptCount');

    const benchmarkId = modal.dataset.benchmarkId;
    const flag = input.value.trim();

    // Validation: Check if flag is entered
    if (!flag) {
        showResult('error', 'Please enter a flag');
        return;
    }

    // Validation: Check flag format
    const validation = validateFlagFormat(flag);
    if (!validation.valid) {
        showResult('error', validation.error);
        return;
    }

    // Disable input and button during submission
    input.disabled = true;
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner"></span> Submitting...';

    try {
        const response = await fetch(`/api/benchmark/${benchmarkId}/submit-flag`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ flag: flag })
        });

        const result = await response.json();

        // Update attempt count
        if (result.attempts && attemptCountEl) {
            attemptCountEl.textContent = result.attempts;
        }

        if (result.correct || result.success) { // Handle both potential API responses
            // Success!
            const time = result.time_to_capture ? `${result.time_to_capture.toFixed(1)}s` : 'N/A';
            showResult('success', `✓ Flag Accepted! Time to capture: ${time}`);

            // Close modal after 2 seconds
            setTimeout(() => {
                closeModal();
            }, 2000);
        } else {
            // Wrong flag
            let message = `✗ Incorrect Flag`;
            if (result.attempts) message += ` (Attempt ${result.attempts})`;

            if (result.hint) {
                message += `\n\nHint: ${result.hint}`;
            } else if (result.message) {
                message += `\n${result.message}`;
            }
            showResult('error', message);

            // Re-enable for retry
            input.disabled = false;
            input.value = '';
            input.focus();
        }

    } catch (error) {
        showResult('error', `Network Error: ${error.message}`);
        input.disabled = false;
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = '📋 Submit Flag';
    }
}

function showResult(type, message) {
    const resultMessage = document.getElementById('resultMessage');
    if (!resultMessage) return;

    resultMessage.className = `result-message ${type}`;
    resultMessage.textContent = message;
    resultMessage.style.display = 'block';

    // Ensure styles are applied (helpers for class based styling)
    if (type === 'success') {
        resultMessage.style.backgroundColor = 'rgba(74, 222, 128, 0.1)';
        resultMessage.style.color = '#4ADE80';
    } else {
        resultMessage.style.backgroundColor = 'rgba(248, 113, 113, 0.1)';
        resultMessage.style.color = '#F87171';
    }
}

// Global scope expose for inline onclicks
window.handleStartClick = handleStartClick;
window.handleStopClick = handleStopClick;
window.handleSubmitFlagClick = handleSubmitFlagClick;
window.showBenchmarkDetails = (id) => {
    const benchmark = allBenchmarks.find(b => b.id === id);
    if (benchmark) import_showBenchmarkDetails(benchmark);
};
window.closeModal = closeModal;
window.submitFlagFromModal = submitFlagFromModal;
window.copyAccessUrl = copyAccessUrl;
window.openInBrowser = openInBrowser;
window.startFromDetails = startFromDetails;

// --- Existing Functions (Adapted) ---

// Show benchmark details modal (Renamed to avoid conflict)
// Show benchmark details modal (Renamed to avoid conflict)
function import_showBenchmarkDetails(benchmark) {
    const modal = document.getElementById('detailsModal');
    if (!modal) return;

    // Helper to safely set text
    const setText = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    };

    // Configuration
    setText('detailsBenchmarkId', benchmark.id);
    setText('detailsCategory', benchmark.category);
    setText('detailsOwasp', benchmark.owasp || 'N/A');
    setText('detailsCwe', benchmark.cwe || 'N/A');
    setText('detailsPort', benchmark.port);
    setText('detailsDifficulty', `${(benchmark.difficulty || 1)}/9`);

    // Testing Instructions variables
    // Extract vuln type from OWASP string if possible
    const vulnType = benchmark.owasp ? benchmark.owasp.split(':')[1] || benchmark.owasp : 'Vulnerability';
    setText('detailsVulnType', vulnType);
    setText('detailsFlagFormat', benchmark.flag_format || 'S7BEN{...}');

    // Update all class-based placeholders
    modal.querySelectorAll('.details-port-number').forEach(el => el.textContent = benchmark.port);
    modal.querySelectorAll('.details-benchmark-id').forEach(el => el.textContent = benchmark.id);

    // Store ID for controls
    modal.dataset.benchmarkId = benchmark.id;

    // Show modal
    modal.classList.add('active');
}

function startFromDetails() {
    const modal = document.getElementById('detailsModal');
    const benchmarkId = modal.dataset.benchmarkId;
    if (benchmarkId) {
        closeDetailsModal();
        handleStartClick(benchmarkId);
        showNotification('info', `Initiating start for ${benchmarkId}...`);
    }
}


// Update category breakdown
function updateCategoryBreakdown() {
    const container = document.getElementById('category-breakdown');
    const categories = ['EASY', 'MED', 'HARD', 'VHARD', 'CVE'];

    container.innerHTML = '';

    categories.forEach(category => {
        const count = allBenchmarks.filter(b => b.category === category).length;
        const percentage = ((count / allBenchmarks.length) * 100).toFixed(1);

        const div = document.createElement('div');
        div.className = 'category-stat';
        div.innerHTML = `
            <span>${category}</span>
            <span>${count} (${percentage}%)</span>
        `;
        container.appendChild(div);
    });
}

// Display statistics
function displayStatistics() {
    // Category stats
    const categoryStats = document.getElementById('category-stats');
    if (statistics.by_category) {
        let html = '<table class="stat-table">';
        Object.entries(statistics.by_category).forEach(([category, count]) => {
            html += `<tr><td>${category}</td><td class="count">${count}</td></tr>`;
        });
        html += '</table>';
        categoryStats.innerHTML = html;
    }

    // OWASP stats
    const owaspStats = document.getElementById('owasp-stats');
    if (statistics.by_owasp) {
        let html = '<table class="stat-table">';
        Object.entries(statistics.by_owasp)
            .sort((a, b) => b[1] - a[1])
            .forEach(([owasp, count]) => {
                html += `<tr><td>${owasp}</td><td class="count">${count}</td></tr>`;
            });
        html += '</table>';
        owaspStats.innerHTML = html;
    }

    // Difficulty stats
    const difficultyStats = document.getElementById('difficulty-stats');
    if (statistics.by_difficulty) {
        let html = '<table class="stat-table">';
        Object.entries(statistics.by_difficulty)
            .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
            .forEach(([diff, count]) => {
                html += `<tr><td>Level ${diff}</td><td class="count">${count}</td></tr>`;
            });
        html += '</table>';
        difficultyStats.innerHTML = html;
    }

    // CWE stats
    const cweStats = document.getElementById('cwe-stats');
    if (statistics.by_cwe) {
        let html = '<table class="stat-table">';
        statistics.by_cwe.forEach(([cwe, count]) => {
            html += `<tr><td>${cwe}</td><td class="count">${count}</td></tr>`;
        });
        html += '</table>';
        cweStats.innerHTML = html;
    }
}

// Initialize charts
function initializeCharts() {
    if (!statistics.by_category) return;

    Chart.defaults.color = COLORS.textSecondary;
    Chart.defaults.borderColor = COLORS.grid;

    // Category Chart
    const categoryCtx = document.getElementById('categoryChart').getContext('2d');
    activeCharts.category = new Chart(categoryCtx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(statistics.by_category),
            datasets: [{
                data: Object.values(statistics.by_category),
                backgroundColor: Object.keys(statistics.by_category).map(c => CATEGORY_COLORS[c] || COLORS.info),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { boxWidth: 12, padding: 15 }
                }
            }
        }
    });

    // OWASP Chart
    const owaspCtx = document.getElementById('owaspChart').getContext('2d');
    activeCharts.owasp = new Chart(owaspCtx, {
        type: 'bar',
        data: {
            labels: Object.keys(statistics.by_owasp),
            datasets: [{
                label: 'Benchmarks',
                data: Object.values(statistics.by_owasp),
                backgroundColor: COLORS.info,
                borderRadius: 2
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: COLORS.grid } },
                x: { grid: { display: false } }
            }
        }
    });

    // Difficulty Chart
    const difficultyCtx = document.getElementById('difficultyChart').getContext('2d');
    const sortedLevels = Object.keys(statistics.by_difficulty).sort();

    activeCharts.difficulty = new Chart(difficultyCtx, {
        type: 'line',
        data: {
            labels: sortedLevels,
            datasets: [{
                label: 'Benchmarks',
                data: sortedLevels.map(k => statistics.by_difficulty[k]),
                borderColor: COLORS.success,
                backgroundColor: 'rgba(74, 222, 128, 0.1)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: COLORS.grid }, beginAtZero: true },
                x: { grid: { color: COLORS.grid } }
            }
        }
    });

    // Phase Chart
    const phaseCtx = document.getElementById('phaseChart').getContext('2d');
    activeCharts.phase = new Chart(phaseCtx, {
        type: 'bar',
        data: {
            labels: Object.keys(statistics.by_phase || {}).map(p => `Phase ${p}`),
            datasets: [{
                label: 'Benchmarks',
                data: Object.values(statistics.by_phase || {}),
                backgroundColor: COLORS.warning,
                borderRadius: 2
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: COLORS.grid }, beginAtZero: true },
                x: { grid: { display: false } }
            }
        }
    });
}

// Apply filters
function applyFilters() {
    const category = document.getElementById('category-filter').value;
    const owasp = document.getElementById('owasp-filter').value;
    const difficulty = document.getElementById('difficulty-filter').value;
    const phase = document.getElementById('phase-filter').value;
    const search = document.getElementById('search-input').value.toLowerCase();

    filteredBenchmarks = allBenchmarks.filter(benchmark => {
        if (category && benchmark.category !== category) return false;
        if (owasp && !benchmark.owasp.includes(owasp)) return false;
        if (difficulty && benchmark.difficulty !== parseInt(difficulty)) return false;
        if (phase && benchmark.phase !== parseInt(phase)) return false;
        if (search && !benchmark.name.toLowerCase().includes(search) &&
            !benchmark.id.toLowerCase().includes(search)) return false;
        return true;
    });

    updateTotalCount();
    displayBenchmarks();

    // Refresh UI status for filtered results
    getContainerStatus().then(updateContainerUI);
}

// Initialize event listeners
function initializeEventListeners() {
    // Filters
    document.getElementById('category-filter').addEventListener('change', applyFilters);
    document.getElementById('owasp-filter').addEventListener('change', applyFilters);
    document.getElementById('difficulty-filter').addEventListener('change', applyFilters);
    document.getElementById('phase-filter').addEventListener('change', applyFilters);
    document.getElementById('search-input').addEventListener('input', applyFilters);

    // Reset filters
    document.getElementById('reset-filters').addEventListener('click', () => {
        document.getElementById('category-filter').value = '';
        document.getElementById('owasp-filter').value = '';
        document.getElementById('difficulty-filter').value = '';
        document.getElementById('phase-filter').value = '';
        document.getElementById('search-input').value = '';
        applyFilters();
    });

    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });

    // View toggle
    document.getElementById('view-grid').addEventListener('click', () => {
        document.getElementById('benchmarks-container').className = 'benchmarks-grid';
        document.getElementById('view-grid').classList.add('active');
        document.getElementById('view-list').classList.remove('active');
    });

    document.getElementById('view-list').addEventListener('click', () => {
        document.getElementById('benchmarks-container').className = 'benchmarks-list';
        document.getElementById('view-list').classList.add('active');
        document.getElementById('view-grid').classList.remove('active');
    });

    // Modal close (handled via window.onclick and inline now, but keeping for safety)
    document.querySelectorAll('.close, .close-modal').forEach(el => {
        el.addEventListener('click', () => {
            closeModal();
            document.getElementById('benchmark-modal').style.display = 'none';
        });
    });
}

// Switch tabs
function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// Show error
function showError(message) {
    const container = document.getElementById('benchmarks-container');
    container.innerHTML = `<div class="loading" style="color: var(--danger-color);">Error: ${message}</div>`;
}

// --- NEW HELPER FUNCTIONS ---

function copyAccessUrl(button) {
    const card = button.closest('.benchmark-card');
    const port = card.dataset.port;
    const url = `http://localhost:${port}`;

    navigator.clipboard.writeText(url).then(() => {
        // Show copied feedback
        const originalText = button.innerHTML;
        button.innerHTML = '✓';
        button.style.color = '#4ADE80';

        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.color = '';
        }, 1500);

        showNotification('success', 'URL copied to clipboard');
    });
}

function openInBrowser(button) {
    const card = button.closest('.benchmark-card');
    const port = card.dataset.port;
    const url = `http://localhost:${port}`;
    window.open(url, '_blank');
}

function validateFlagFormat(flag) {
    // Basic format check
    if (!flag.startsWith('S7BEN{')) {
        return {
            valid: false,
            error: 'Flag must start with S7BEN{'
        };
    }

    if (!flag.endsWith('}')) {
        return {
            valid: false,
            error: 'Flag must end with }'
        };
    }

    // Extract content between braces
    const content = flag.substring(6, flag.length - 1);

    if (content.length === 0) {
        return {
            valid: false,
            error: 'Flag content cannot be empty'
        };
    }

    // Content can be: letters, numbers, underscores, hyphens
    if (!/^[a-zA-Z0-9_\-]+$/.test(content)) {
        return {
            valid: false,
            error: 'Flag can only contain letters, numbers, underscores, and hyphens'
        };
    }

    return { valid: true };
}

function handleApiError(error, operation) {
    let message = '';

    if (error.message === 'Failed to fetch') {
        message = `Cannot connect to Dashboard API at localhost:5500.\n\nIs the server running?\n\nStart it with: python dashboard/app.py`;
    } else if (error.status === 404) {
        message = `Benchmark not found.\n\nThis benchmark may not be installed or the ID is incorrect.`;
    } else if (error.status === 500) {
        message = `Server error during ${operation}.\n\nCheck the dashboard logs for details.`;
    } else if (error.message.includes('timeout')) {
        message = `Operation timed out.\n\nThe container may be taking longer than expected to ${operation}.`;
    } else {
        message = `${operation} failed: ${error.message}`;
    }

    return message;
}

function showNotification(type, message) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}
