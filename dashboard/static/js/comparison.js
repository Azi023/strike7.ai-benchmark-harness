// ================================================================
// Strike7 Model Comparison Dashboard — JavaScript
// Vanilla JS, Chart.js 4.4.0, fetch() API
// ================================================================

const API_BASE = `${window.location.origin}/api`;

// Provider colors for charts and badges
const PROVIDER_COLORS = {
    google:    { bg: 'rgba(66, 133, 244, 0.7)',  border: '#4285F4' },
    anthropic: { bg: 'rgba(212, 165, 116, 0.7)', border: '#D4A574' },
    openai:    { bg: 'rgba(16, 163, 127, 0.7)',  border: '#10A37F' },
};

const TIER_ORDER = ['EASY', 'MED', 'HARD', 'VHARD', 'CVE'];

// State
let summaryData = [];
let matrixData = { matrix: {}, models: [], benchmarks: [] };
let modelsData = [];
let runsData = [];
let leaderboard = [];
let activeCharts = {};
let currentSort = { field: 'pass_rate', asc: false };
let enumsData = { failure_reasons: [], failure_stages: [], difficulty_tiers: [] };
let campaignsData = [];
let groupByProduct = false;
let failureData = { stage_funnel: [], reason_breakdown: [], total_failures: 0 };

// ================================================================
// Init
// ================================================================

document.addEventListener('DOMContentLoaded', async () => {
    initTabs();
    initFilters();
    initSortHeaders();
    initLeaderboardToggle();
    loadFiltersFromURL();
    await Promise.all([fetchEnums(), fetchCampaigns()]);
    await refreshAll();
    await fetchActiveRuns();

    // Auto-refresh every 10 seconds for dashboard data
    setInterval(async () => {
        try {
            await refreshAll();
        } catch (e) {
            console.warn('Auto-refresh failed:', e);
        }
    }, 10000);

    // Active runs poll every 3 seconds for real-time step tracking
    setInterval(async () => {
        try {
            await fetchActiveRuns();
        } catch (e) {
            console.warn('Active runs poll failed:', e);
        }
    }, 3000);
});

async function refreshAll() {
    await Promise.all([
        fetchSummary(),
        fetchMatrix(),
        fetchModels(),
        fetchRecentRuns(),
        fetchFailureAnalysis(),
    ]);
    buildLeaderboard();
    renderLeaderboard();
    renderHeatmap();
    renderCharts();
    renderRecentRuns();
    updateHeaderStats();
    populateBenchmarkFilter();
    populateProductFilter();
    populateCampaignFilter();
}

// ================================================================
// Tabs
// ================================================================

function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelector(`.tab-btn[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// ================================================================
// Filters
// ================================================================

function initFilters() {
    document.getElementById('filter-provider').addEventListener('change', onFilterChange);
    document.getElementById('filter-tier').addEventListener('change', onFilterChange);
    document.getElementById('filter-benchmark').addEventListener('change', onFilterChange);
    document.getElementById('filter-product').addEventListener('change', onFilterChange);
    document.getElementById('filter-campaign').addEventListener('change', onFilterChange);
    document.getElementById('btn-reset-filters').addEventListener('click', resetFilters);
    document.getElementById('btn-refresh').addEventListener('click', refreshAll);
    document.getElementById('btn-generate-report').addEventListener('click', generateReport);
}

function getFilters() {
    return {
        provider: document.getElementById('filter-provider').value,
        tier: document.getElementById('filter-tier').value,
        benchmark: document.getElementById('filter-benchmark').value,
        product: document.getElementById('filter-product').value,
        campaign: document.getElementById('filter-campaign').value,
    };
}

async function onFilterChange() {
    syncFiltersToURL();
    await Promise.all([fetchSummary(), fetchMatrix(), fetchRecentRuns(), fetchFailureAnalysis()]);
    buildLeaderboard();
    renderLeaderboard();
    renderHeatmap();
    renderCharts();
    renderRecentRuns();
    updateHeaderStats();
}

function resetFilters() {
    document.getElementById('filter-provider').value = '';
    document.getElementById('filter-tier').value = '';
    document.getElementById('filter-benchmark').value = '';
    document.getElementById('filter-product').value = '';
    document.getElementById('filter-campaign').value = '';
    onFilterChange();
}

function syncFiltersToURL() {
    const f = getFilters();
    const params = new URLSearchParams();
    Object.entries(f).forEach(([k, v]) => { if (v) params.set(k, v); });
    window.history.replaceState({}, '', params.toString() ? '?' + params : location.pathname);
}

function loadFiltersFromURL() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('provider')) document.getElementById('filter-provider').value = params.get('provider');
    if (params.get('tier')) document.getElementById('filter-tier').value = params.get('tier');
    if (params.get('product')) document.getElementById('filter-product').value = params.get('product');
    if (params.get('campaign')) document.getElementById('filter-campaign').value = params.get('campaign');
    // benchmark is populated after data loads, will be set via populateBenchmarkFilter
}

function populateBenchmarkFilter() {
    const select = document.getElementById('filter-benchmark');
    const current = select.value;
    const benchmarks = new Set();
    summaryData.forEach(s => benchmarks.add(s.benchmark_id));
    runsData.forEach(r => benchmarks.add(r.benchmark_id));

    // Keep first option, remove rest
    while (select.options.length > 1) select.remove(1);

    const sorted = [...benchmarks].sort((a, b) => {
        const tierA = TIER_ORDER.indexOf(a.split('-')[1]);
        const tierB = TIER_ORDER.indexOf(b.split('-')[1]);
        return tierA !== tierB ? tierA - tierB : a.localeCompare(b);
    });

    sorted.forEach(id => {
        const opt = document.createElement('option');
        opt.value = id;
        opt.textContent = id;
        select.appendChild(opt);
    });

    select.value = current;
}

// ================================================================
// API Calls
// ================================================================

function buildQuery(extra) {
    const f = getFilters();
    const params = new URLSearchParams();
    if (f.provider) params.set('provider', f.provider);
    if (f.tier) params.set('difficulty_tier', f.tier);
    if (f.benchmark) params.set('benchmark_id', f.benchmark);
    if (f.product) params.set('product_name', f.product);
    if (f.campaign) params.set('campaign_id', f.campaign);
    if (extra) Object.entries(extra).forEach(([k, v]) => params.set(k, v));
    return params.toString();
}

async function fetchSummary() {
    try {
        const q = buildQuery();
        const res = await fetch(`${API_BASE}/comparison/summary${q ? '?' + q : ''}`);
        const data = await res.json();
        summaryData = data.summaries || [];
    } catch (e) {
        console.error('Failed to fetch summary:', e);
        summaryData = [];
    }
}

async function fetchMatrix() {
    try {
        const res = await fetch(`${API_BASE}/comparison/matrix`);
        const data = await res.json();
        matrixData = data;
    } catch (e) {
        console.error('Failed to fetch matrix:', e);
        matrixData = { matrix: {}, models: [], benchmarks: [] };
    }
}

async function fetchModels() {
    try {
        const res = await fetch(`${API_BASE}/comparison/models`);
        const data = await res.json();
        modelsData = data.models || [];
    } catch (e) {
        console.error('Failed to fetch models:', e);
        modelsData = [];
    }
}

async function fetchRecentRuns() {
    try {
        const q = buildQuery({ limit: '20' });
        const res = await fetch(`${API_BASE}/comparison/runs${q ? '?' + q : ''}`);
        const data = await res.json();
        runsData = data.runs || [];
    } catch (e) {
        console.error('Failed to fetch runs:', e);
        runsData = [];
    }
}

async function fetchEnums() {
    try {
        const res = await fetch(`${API_BASE}/comparison/enums`);
        const data = await res.json();
        enumsData = data;
    } catch (e) {
        console.error('Failed to fetch enums:', e);
    }
}

async function fetchCampaigns() {
    try {
        const res = await fetch(`${API_BASE}/comparison/campaigns`);
        const data = await res.json();
        campaignsData = data.campaigns || [];
    } catch (e) {
        console.error('Failed to fetch campaigns:', e);
        campaignsData = [];
    }
}

function populateProductFilter() {
    const select = document.getElementById('filter-product');
    const current = select.value;
    const products = new Set();

    runsData.forEach(r => { if (r.product_name) products.add(r.product_name); });
    summaryData.forEach(s => { if (s.product_name) products.add(s.product_name); });
    campaignsData.forEach(c => { if (c.product_name) products.add(c.product_name); });

    while (select.options.length > 1) select.remove(1);
    [...products].sort().forEach(name => {
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = name;
        select.appendChild(opt);
    });
    select.value = current;
}

function populateCampaignFilter() {
    const select = document.getElementById('filter-campaign');
    const current = select.value;

    while (select.options.length > 1) select.remove(1);
    campaignsData.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.campaign_id;
        opt.textContent = `${c.campaign_name} (${c.total_runs || 0} runs)`;
        select.appendChild(opt);
    });
    select.value = current;
}

// ================================================================
// Report Generation
// ================================================================

async function generateReport() {
    const btn = document.getElementById('btn-generate-report');
    const original = btn.textContent;
    btn.textContent = 'Generating...';
    btn.disabled = true;

    try {
        const q = buildQuery({ format: 'markdown', compare_previous: 'true' });
        const res = await fetch(`${API_BASE}/comparison/report${q ? '?' + q : ''}`);

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
        const a = document.createElement('a');
        a.href = url;
        a.download = `Strike7_Report_${date}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (e) {
        console.error('Failed to generate report:', e);
        alert('Failed to generate report. Check console for details.');
    } finally {
        btn.textContent = original;
        btn.disabled = false;
    }
}

// ================================================================
// Failure Analysis
// ================================================================

async function fetchFailureAnalysis() {
    try {
        const q = buildQuery();
        const res = await fetch(`${API_BASE}/comparison/failure-analysis${q ? '?' + q : ''}`);
        const data = await res.json();
        failureData = {
            stage_funnel: data.stage_funnel || [],
            reason_breakdown: data.reason_breakdown || [],
            total_failures: data.total_failures || 0,
        };
    } catch (e) {
        console.error('Failed to fetch failure analysis:', e);
        failureData = { stage_funnel: [], reason_breakdown: [], total_failures: 0 };
    }
}

function renderFailureFunnel() {
    if (failureData.stage_funnel.length === 0) {
        if (activeCharts['failureFunnelChart']) {
            activeCharts['failureFunnelChart'].destroy();
            delete activeCharts['failureFunnelChart'];
        }
        return;
    }

    const pipelineOrder = ['recon', 'analysis', 'exploitation', 'flag_extraction', 'flag_submission'];
    const stageMap = {};
    failureData.stage_funnel.forEach(s => { stageMap[s.stage] = s.count; });

    const labels = pipelineOrder.filter(s => stageMap[s]);
    const data = labels.map(s => stageMap[s]);

    // Red gradient — pipeline progression
    const colors = [
        'rgba(248, 113, 113, 0.5)',
        'rgba(239, 68, 68, 0.55)',
        'rgba(220, 38, 38, 0.6)',
        'rgba(185, 28, 28, 0.65)',
        'rgba(153, 27, 27, 0.7)',
    ];

    createOrUpdate('failureFunnelChart', 'bar', {
        labels: labels.map(s => s.replace('_', ' ')),
        datasets: [{
            label: 'Failures',
            data,
            backgroundColor: labels.map((_, i) => colors[i % colors.length]),
            borderColor: labels.map((_, i) => colors[i % colors.length].replace(/[\d.]+\)$/, '1)')),
            borderWidth: 1,
        }]
    }, {
        indexAxis: 'y',
        scales: {
            x: { beginAtZero: true, grid: { color: '#252525' } },
            y: { grid: { display: false } },
        },
        plugins: { legend: { display: false } },
    });
}

function renderFailureReasons() {
    if (failureData.reason_breakdown.length === 0) {
        if (activeCharts['failureReasonChart']) {
            activeCharts['failureReasonChart'].destroy();
            delete activeCharts['failureReasonChart'];
        }
        return;
    }

    // Top 10 reasons sorted by count desc
    const top = failureData.reason_breakdown
        .slice()
        .sort((a, b) => b.count - a.count)
        .slice(0, 10);

    const labels = top.map(r => r.reason.replace(/_/g, ' '));
    const data = top.map(r => r.count);

    createOrUpdate('failureReasonChart', 'bar', {
        labels,
        datasets: [{
            label: 'Count',
            data,
            backgroundColor: 'rgba(251, 191, 36, 0.5)',
            borderColor: 'rgba(251, 191, 36, 1)',
            borderWidth: 1,
        }]
    }, {
        indexAxis: 'y',
        scales: {
            x: { beginAtZero: true, grid: { color: '#252525' } },
            y: { grid: { display: false } },
        },
        plugins: { legend: { display: false } },
    });
}

// ================================================================
// Leaderboard Toggle
// ================================================================

function initLeaderboardToggle() {
    document.getElementById('btn-group-model').addEventListener('click', () => {
        groupByProduct = false;
        document.getElementById('btn-group-model').classList.add('active');
        document.getElementById('btn-group-product').classList.remove('active');
        buildLeaderboard();
        renderLeaderboard();
    });
    document.getElementById('btn-group-product').addEventListener('click', () => {
        groupByProduct = true;
        document.getElementById('btn-group-product').classList.add('active');
        document.getElementById('btn-group-model').classList.remove('active');
        buildLeaderboard();
        renderLeaderboard();
    });
}

// ================================================================
// Leaderboard
// ================================================================

function buildLeaderboard() {
    const groupKey = groupByProduct ? 'product_name' : 'model_name';
    const byGroup = {};

    summaryData.forEach(s => {
        const key = groupByProduct ? s.product_name : s.model_name;
        if (!key) return; // skip null product_name entries in product mode
        if (!byGroup[key]) {
            byGroup[key] = {
                model_name: groupByProduct ? key : s.model_name,
                provider: s.provider,
                product_name: s.product_name || null,
                total_runs: 0,
                successful_runs: 0,
                time_sum: 0,
                time_count: 0,
                tokens_sum: 0,
                tokens_count: 0,
                steps_sum: 0,
                steps_count: 0,
                cost_sum: 0,
                cost_count: 0,
            };
        }
        const m = byGroup[key];
        // In product mode, provider may vary — use 'mixed' if providers differ
        if (groupByProduct && m.provider !== s.provider && m.total_runs > 0) {
            m.provider = 'mixed';
        }
        m.total_runs += s.total_runs || 0;
        m.successful_runs += s.successful_runs || 0;
        if (s.avg_time_s != null) { m.time_sum += s.avg_time_s * s.total_runs; m.time_count += s.total_runs; }
        if (s.avg_tokens != null) { m.tokens_sum += s.avg_tokens * s.total_runs; m.tokens_count += s.total_runs; }
        if (s.avg_steps != null) { m.steps_sum += s.avg_steps * s.total_runs; m.steps_count += s.total_runs; }
        if (s.avg_cost_usd != null) { m.cost_sum += s.avg_cost_usd * s.total_runs; m.cost_count += s.total_runs; }
    });

    leaderboard = Object.values(byGroup).map(m => ({
        model_name: m.model_name,
        provider: m.provider,
        product_name: m.product_name,
        total_runs: m.total_runs,
        pass_rate: m.total_runs > 0 ? m.successful_runs / m.total_runs : 0,
        avg_time_s: m.time_count > 0 ? m.time_sum / m.time_count : null,
        avg_tokens: m.tokens_count > 0 ? Math.round(m.tokens_sum / m.tokens_count) : null,
        avg_steps: m.steps_count > 0 ? Math.round(m.steps_sum / m.steps_count * 10) / 10 : null,
        avg_cost_usd: m.cost_count > 0 ? m.cost_sum / m.cost_count : null,
    }));

    sortLeaderboard();
}

function sortLeaderboard() {
    const { field, asc } = currentSort;
    leaderboard.sort((a, b) => {
        let va = a[field], vb = b[field];
        if (va == null) va = asc ? Infinity : -Infinity;
        if (vb == null) vb = asc ? Infinity : -Infinity;
        if (typeof va === 'string') return asc ? va.localeCompare(vb) : vb.localeCompare(va);
        return asc ? va - vb : vb - va;
    });
}

function initSortHeaders() {
    document.querySelectorAll('.leaderboard-table th.sortable').forEach(th => {
        th.addEventListener('click', () => {
            const field = th.dataset.sort;
            if (currentSort.field === field) {
                currentSort.asc = !currentSort.asc;
            } else {
                currentSort.field = field;
                currentSort.asc = field === 'model_name' || field === 'provider';
            }
            sortLeaderboard();
            renderLeaderboard();
            // Update header UI
            document.querySelectorAll('.leaderboard-table th.sortable').forEach(h => {
                h.classList.remove('active-sort', 'sort-asc');
            });
            th.classList.add('active-sort');
            if (currentSort.asc) th.classList.add('sort-asc');
        });
    });
}

function renderLeaderboard() {
    const tbody = document.getElementById('leaderboard-body');
    const empty = document.getElementById('leaderboard-empty');

    if (leaderboard.length === 0) {
        tbody.innerHTML = '';
        empty.style.display = 'block';
        return;
    }

    empty.style.display = 'none';
    tbody.innerHTML = leaderboard.map((m, i) => {
        const rank = i + 1;
        const rankClass = rank <= 3 ? `rank-medal rank-${rank}` : '';
        const passClass = getPassRateClass(m.pass_rate);
        const providerClass = `provider-${m.provider}`;

        const productLabel = m.product_name && m.product_name !== m.model_name
            ? `<span class="product-label">${esc(m.product_name)}</span> `
            : '';

        return `<tr>
            <td class="col-rank ${rankClass}">${rank}</td>
            <td class="col-model">${productLabel}<span class="model-name">${esc(m.model_name)}</span></td>
            <td class="col-provider"><span class="provider-badge ${providerClass}">${esc(m.provider)}</span></td>
            <td class="col-runs mono-val">${m.total_runs}</td>
            <td class="col-pass"><span class="pass-rate ${passClass}">${(m.pass_rate * 100).toFixed(1)}%</span></td>
            <td class="col-time mono-val">${m.avg_time_s != null ? m.avg_time_s.toFixed(1) + 's' : '—'}</td>
            <td class="col-tokens mono-val">${m.avg_tokens != null ? m.avg_tokens.toLocaleString() : '—'}</td>
            <td class="col-steps mono-val">${m.avg_steps != null ? m.avg_steps : '—'}</td>
            <td class="col-cost mono-val">${m.avg_cost_usd != null ? '$' + m.avg_cost_usd.toFixed(4) : '—'}</td>
        </tr>`;
    }).join('');
}

function getPassRateClass(rate) {
    if (rate >= 0.7) return 'pass-rate-high';
    if (rate >= 0.4) return 'pass-rate-mid';
    if (rate > 0) return 'pass-rate-low';
    return 'pass-rate-zero';
}

// ================================================================
// Heatmap
// ================================================================

function renderHeatmap() {
    const grid = document.getElementById('heatmap-grid');
    const empty = document.getElementById('heatmap-empty');
    const info = document.getElementById('heatmap-info');
    const filters = getFilters();

    let models = matrixData.models || [];
    let benchmarks = matrixData.benchmarks || [];
    const matrix = matrixData.matrix || {};

    // Apply filters
    if (filters.provider) {
        models = models.filter(m => {
            const first = Object.values(matrix[m] || {})[0];
            return first && first.provider === filters.provider;
        });
    }
    if (filters.tier) {
        benchmarks = benchmarks.filter(b => b.includes(`-${filters.tier}-`));
    }
    if (filters.benchmark) {
        benchmarks = benchmarks.filter(b => b === filters.benchmark);
    }

    // Sort benchmarks by tier order
    benchmarks.sort((a, b) => {
        const ta = TIER_ORDER.indexOf(a.split('-')[1]);
        const tb = TIER_ORDER.indexOf(b.split('-')[1]);
        return ta !== tb ? ta - tb : a.localeCompare(b);
    });

    if (models.length === 0 || benchmarks.length === 0) {
        grid.innerHTML = '';
        empty.style.display = 'block';
        info.textContent = '';
        return;
    }

    empty.style.display = 'none';
    info.textContent = `${models.length} models × ${benchmarks.length} benchmarks`;

    const cols = benchmarks.length + 1; // +1 for model name column
    grid.style.gridTemplateColumns = `180px repeat(${benchmarks.length}, 80px)`;

    let html = '';

    // Header row: empty corner + benchmark names
    html += '<div class="heatmap-header"></div>'; // corner
    benchmarks.forEach(b => {
        const tier = b.split('-')[1];
        const shortId = b.replace('S7BEN-', '');
        html += `<div class="heatmap-header heatmap-header-benchmark">
            <span>${shortId}</span>
        </div>`;
    });

    // Data rows
    models.forEach(model => {
        html += `<div class="heatmap-header heatmap-header-model">${esc(model)}</div>`;
        benchmarks.forEach(bench => {
            const cell = (matrix[model] || {})[bench];
            if (!cell) {
                html += `<div class="heatmap-cell cell-none"
                    data-model="${esc(model)}" data-bench="${esc(bench)}"
                    onmouseenter="showTooltip(event, this)" onmouseleave="hideTooltip()">—</div>`;
            } else {
                const cellClass = cell.pass_rate >= 1.0 ? 'cell-pass'
                    : cell.pass_rate > 0 ? 'cell-partial'
                    : 'cell-fail';
                const label = cell.pass_rate >= 1.0 ? '✓'
                    : cell.pass_rate > 0 ? `${Math.round(cell.pass_rate * 100)}%`
                    : '✗';
                html += `<div class="heatmap-cell ${cellClass}"
                    data-model="${esc(model)}" data-bench="${esc(bench)}"
                    data-runs="${cell.total_runs}" data-successes="${cell.successes}"
                    data-rate="${cell.pass_rate}" data-time="${cell.avg_time_s || ''}"
                    data-cost="${cell.avg_cost_usd || ''}"
                    onmouseenter="showTooltip(event, this)" onmouseleave="hideTooltip()">${label}</div>`;
            }
        });
    });

    grid.innerHTML = html;
}

// Tooltip for heatmap cells
function showTooltip(event, el) {
    const tooltip = document.getElementById('cell-tooltip');
    const model = el.dataset.model;
    const bench = el.dataset.bench;
    const runs = el.dataset.runs;

    let content = `<div class="tt-title">${model} → ${bench}</div>`;
    if (!runs) {
        content += '<div class="tt-row"><span class="tt-label">Not tested</span></div>';
    } else {
        const rate = parseFloat(el.dataset.rate);
        const time = el.dataset.time;
        const cost = el.dataset.cost;
        content += `<div class="tt-row"><span class="tt-label">Runs:</span><span class="tt-val">${runs}</span></div>`;
        content += `<div class="tt-row"><span class="tt-label">Pass rate:</span><span class="tt-val">${(rate * 100).toFixed(0)}%</span></div>`;
        if (time) content += `<div class="tt-row"><span class="tt-label">Avg time:</span><span class="tt-val">${parseFloat(time).toFixed(1)}s</span></div>`;
        if (cost) content += `<div class="tt-row"><span class="tt-label">Avg cost:</span><span class="tt-val">$${parseFloat(cost).toFixed(4)}</span></div>`;
    }

    tooltip.innerHTML = content;
    tooltip.style.display = 'block';

    // Position near cursor
    const rect = tooltip.getBoundingClientRect();
    let x = event.clientX + 12;
    let y = event.clientY + 12;
    if (x + rect.width > window.innerWidth) x = event.clientX - rect.width - 12;
    if (y + rect.height > window.innerHeight) y = event.clientY - rect.height - 12;
    tooltip.style.left = x + 'px';
    tooltip.style.top = y + 'px';
}

function hideTooltip() {
    document.getElementById('cell-tooltip').style.display = 'none';
}

// Make tooltip functions globally accessible for inline handlers
window.showTooltip = showTooltip;
window.hideTooltip = hideTooltip;

// ================================================================
// Charts
// ================================================================

function renderCharts() {
    const empty = document.getElementById('charts-empty');
    if (leaderboard.length === 0) {
        empty.style.display = 'block';
        destroyCharts();
        return;
    }
    empty.style.display = 'none';

    const labels = leaderboard.map(m => m.model_name);
    const providers = leaderboard.map(m => m.provider);
    const bgColors = providers.map(p => (PROVIDER_COLORS[p] || PROVIDER_COLORS.openai).bg);
    const borderColors = providers.map(p => (PROVIDER_COLORS[p] || PROVIDER_COLORS.openai).border);

    Chart.defaults.color = '#ACACAC';
    Chart.defaults.borderColor = '#252525';

    // Pass Rate
    createOrUpdate('passRateChart', 'bar', {
        labels,
        datasets: [{
            label: 'Pass Rate (%)',
            data: leaderboard.map(m => (m.pass_rate * 100).toFixed(1)),
            backgroundColor: bgColors,
            borderColor: borderColors,
            borderWidth: 1,
        }]
    }, {
        scales: {
            y: { beginAtZero: true, max: 100, grid: { color: '#252525' } },
            x: { grid: { display: false } },
        },
        plugins: { legend: { display: false } },
    });

    // Average Time
    createOrUpdate('timeChart', 'bar', {
        labels,
        datasets: [{
            label: 'Avg Time (s)',
            data: leaderboard.map(m => m.avg_time_s != null ? m.avg_time_s.toFixed(1) : 0),
            backgroundColor: bgColors,
            borderColor: borderColors,
            borderWidth: 1,
        }]
    }, {
        scales: {
            y: { beginAtZero: true, grid: { color: '#252525' } },
            x: { grid: { display: false } },
        },
        plugins: { legend: { display: false } },
    });

    // Average Cost
    createOrUpdate('costChart', 'bar', {
        labels,
        datasets: [{
            label: 'Avg Cost ($)',
            data: leaderboard.map(m => m.avg_cost_usd != null ? m.avg_cost_usd.toFixed(4) : 0),
            backgroundColor: bgColors,
            borderColor: borderColors,
            borderWidth: 1,
        }]
    }, {
        scales: {
            y: { beginAtZero: true, grid: { color: '#252525' } },
            x: { grid: { display: false } },
        },
        plugins: { legend: { display: false } },
    });

    // Efficiency scatter: Cost (x) vs Pass Rate (y)
    const scatterData = leaderboard
        .filter(m => m.avg_cost_usd != null)
        .map(m => ({
            x: m.avg_cost_usd,
            y: m.pass_rate * 100,
            label: m.model_name,
            provider: m.provider,
        }));

    // Group scatter points by provider for coloring
    const scatterByProvider = {};
    scatterData.forEach(p => {
        if (!scatterByProvider[p.provider]) scatterByProvider[p.provider] = [];
        scatterByProvider[p.provider].push(p);
    });

    const scatterDatasets = Object.entries(scatterByProvider).map(([prov, pts]) => ({
        label: prov,
        data: pts,
        backgroundColor: (PROVIDER_COLORS[prov] || PROVIDER_COLORS.openai).bg,
        borderColor: (PROVIDER_COLORS[prov] || PROVIDER_COLORS.openai).border,
        borderWidth: 2,
        pointRadius: 8,
        pointHoverRadius: 12,
    }));

    createOrUpdate('efficiencyChart', 'scatter', {
        datasets: scatterDatasets,
    }, {
        scales: {
            x: {
                title: { display: true, text: 'Avg Cost (USD)', color: '#ACACAC' },
                grid: { color: '#252525' },
            },
            y: {
                title: { display: true, text: 'Pass Rate (%)', color: '#ACACAC' },
                beginAtZero: true,
                max: 100,
                grid: { color: '#252525' },
            },
        },
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: { boxWidth: 10, padding: 15 },
            },
            tooltip: {
                callbacks: {
                    label: (ctx) => {
                        const pt = ctx.raw;
                        return `${pt.label}: ${pt.y.toFixed(1)}% pass, $${pt.x.toFixed(4)}`;
                    }
                }
            }
        },
    });

    // Failure charts
    renderFailureFunnel();
    renderFailureReasons();
}

function createOrUpdate(canvasId, type, data, options) {
    if (activeCharts[canvasId]) {
        activeCharts[canvasId].destroy();
    }
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    activeCharts[canvasId] = new Chart(ctx, {
        type,
        data,
        options: { responsive: true, maintainAspectRatio: true, ...options },
    });
}

function destroyCharts() {
    Object.values(activeCharts).forEach(c => c.destroy());
    activeCharts = {};
}

// ================================================================
// Recent Runs
// ================================================================

function renderRecentRuns() {
    const tbody = document.getElementById('recent-runs-body');
    const empty = document.getElementById('recent-runs-empty');

    if (runsData.length === 0) {
        tbody.innerHTML = '';
        empty.style.display = 'block';
        return;
    }

    empty.style.display = 'none';
    tbody.innerHTML = runsData.map(r => {
        const ts = r.run_timestamp ? new Date(r.run_timestamp).toLocaleString() : '—';
        const result = r.flag_captured ? '<span class="result-pass">CAPTURED</span>' : '<span class="result-fail">FAILED</span>';
        const duration = r.total_duration_s != null ? r.total_duration_s.toFixed(0) + 's' : '—';
        const tokens = r.total_tokens != null ? r.total_tokens.toLocaleString() : '—';
        const cost = r.cost_usd != null ? '$' + r.cost_usd.toFixed(4) : '—';
        const providerClass = `provider-${r.provider}`;
        const steps = r.steps_taken != null ? r.steps_taken : (r.total_steps != null ? r.total_steps : '—');
        const loopBadge = r.loop_detected ? ' <span class="loop-badge">LOOP</span>' : '';
        const clickable = r.run_id ? ` onclick="showRunDetail('${esc(r.run_id)}')" style="cursor:pointer;"` : '';

        const productTag = r.product_name && r.product_name !== r.model_name
            ? `<span class="product-label">${esc(r.product_name)}</span> `
            : '';

        return `<tr${clickable}>
            <td class="mono-val" style="font-size:0.78rem;">${ts}</td>
            <td class="mono-val">${esc(r.benchmark_id)}</td>
            <td>${productTag}<span class="provider-badge ${providerClass}">${esc(r.provider)}</span> ${esc(r.model_name)}</td>
            <td>${result}</td>
            <td class="mono-val">${steps}${loopBadge}</td>
            <td class="mono-val">${duration}</td>
            <td class="mono-val">${tokens}</td>
            <td class="mono-val">${cost}</td>
        </tr>`;
    }).join('');
}

// ================================================================
// Header Stats
// ================================================================

function updateHeaderStats() {
    const totalRuns = leaderboard.reduce((s, m) => s + m.total_runs, 0);
    const modelsCount = leaderboard.length;

    let totalSuccessful = 0;
    let totalAll = 0;
    summaryData.forEach(s => {
        totalSuccessful += s.successful_runs || 0;
        totalAll += s.total_runs || 0;
    });
    const overallPassRate = totalAll > 0 ? ((totalSuccessful / totalAll) * 100).toFixed(1) : '0.0';

    let totalCost = 0;
    summaryData.forEach(s => { totalCost += s.total_cost_usd || 0; });

    document.getElementById('total-runs').textContent = totalRuns;
    document.getElementById('models-tested').textContent = modelsCount;
    document.getElementById('overall-pass-rate').textContent = overallPassRate + '%';
    document.getElementById('total-cost').textContent = '$' + totalCost.toFixed(2);
}

// ================================================================
// Utility
// ================================================================

function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

// ================================================================
// Active Runs (Real-time)
// ================================================================

async function fetchActiveRuns() {
    try {
        const res = await fetch(`${API_BASE}/comparison/runs/active`);
        const data = await res.json();
        renderActiveRuns(data.active_runs || []);
    } catch (e) {
        console.warn('Failed to fetch active runs:', e);
    }
}

function renderActiveRuns(runs) {
    const section = document.getElementById('active-runs-section');
    const container = document.getElementById('active-runs-container');
    const badge = document.getElementById('active-runs-count');

    if (runs.length === 0) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    badge.textContent = runs.length;

    container.innerHTML = runs.map(r => {
        const elapsed = r.run_timestamp
            ? Math.round((Date.now() - new Date(r.run_timestamp).getTime()) / 1000)
            : 0;
        const elapsedStr = elapsed > 60
            ? `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`
            : `${elapsed}s`;
        const providerClass = `provider-${r.provider || 'unknown'}`;
        const stepsHtml = (r.live_steps || []).slice(-5).map(s =>
            `<div class="live-step">
                <span class="step-num">#${s.step_number}</span>
                <span class="step-method method-${(s.method || '').toLowerCase()}">${esc(s.method)}</span>
                <span class="step-path">${esc(s.path)}</span>
                <span class="step-status status-${Math.floor((s.status_code || 0) / 100)}xx">${s.status_code || '?'}</span>
                <span class="step-time">${s.duration_ms ? s.duration_ms.toFixed(0) + 'ms' : ''}</span>
            </div>`
        ).join('');

        return `<div class="active-run-card">
            <div class="active-run-header">
                <div>
                    <span class="provider-badge ${providerClass}">${esc(r.provider || 'unknown')}</span>
                    <strong>${esc(r.model_name || 'unknown')}</strong>
                </div>
                <div class="active-run-bench">${esc(r.benchmark_id)}</div>
            </div>
            <div class="active-run-stats">
                <span class="active-stat"><strong>${r.total_steps || 0}</strong> steps</span>
                <span class="active-stat"><strong>${r.unique_paths || 0}</strong> unique paths</span>
                <span class="active-stat"><strong>${elapsedStr}</strong> elapsed</span>
            </div>
            <div class="live-steps-list">${stepsHtml || '<div class="no-steps">Waiting for first request...</div>'}</div>
        </div>`;
    }).join('');
}

// ================================================================
// Run Detail Modal
// ================================================================

async function showRunDetail(runId) {
    const modal = document.getElementById('run-detail-modal');
    const body = document.getElementById('modal-body');
    const title = document.getElementById('modal-title');

    modal.style.display = 'flex';
    body.innerHTML = '<div class="modal-loading">Loading run details...</div>';

    try {
        const res = await fetch(`${API_BASE}/comparison/runs/${runId}/detail`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        renderRunDetail(data, title, body);
    } catch (e) {
        body.innerHTML = `<div class="modal-error">Failed to load: ${esc(e.message)}</div>`;
    }
}

function renderRunDetail(data, titleEl, bodyEl) {
    const run = data.run || {};
    const steps = data.steps || [];
    const flags = data.flag_attempts || [];
    const metrics = data.metrics || {};

    const result = run.flag_captured ? 'CAPTURED' : 'FAILED';
    const resultClass = run.flag_captured ? 'result-pass' : 'result-fail';
    titleEl.textContent = `${run.benchmark_id || 'Unknown'} — ${run.model_name || 'Unknown'}`;

    // Metrics summary
    const metricsHtml = `
        <div class="detail-metrics">
            <div class="detail-metric">
                <span class="dm-value">${metrics.total_steps || 0}</span>
                <span class="dm-label">Total Steps</span>
            </div>
            <div class="detail-metric">
                <span class="dm-value">${metrics.unique_paths || 0}</span>
                <span class="dm-label">Unique Paths</span>
            </div>
            <div class="detail-metric">
                <span class="dm-value">${metrics.loop_count || 0}</span>
                <span class="dm-label">Loops</span>
            </div>
            <div class="detail-metric">
                <span class="dm-value">${metrics.avg_step_duration_ms || 0}ms</span>
                <span class="dm-label">Avg Step Time</span>
            </div>
            <div class="detail-metric">
                <span class="dm-value ${resultClass}">${result}</span>
                <span class="dm-label">Result</span>
            </div>
            <div class="detail-metric">
                <span class="dm-value">${run.total_duration_s ? run.total_duration_s.toFixed(0) + 's' : '—'}</span>
                <span class="dm-label">Duration</span>
            </div>
        </div>`;

    // Loop warnings
    let loopHtml = '';
    if (metrics.loops && metrics.loops.length > 0) {
        loopHtml = `<div class="loop-warning">
            <strong>Loop Detected:</strong>
            ${metrics.loops.map(l =>
                `<span class="loop-detail">${esc(l.path)} repeated ${l.count}x starting at step #${l.start_step}</span>`
            ).join(', ')}
        </div>`;
    }

    // Run info bar
    const infoHtml = `
        <div class="detail-info">
            <span><strong>Provider:</strong> ${esc(run.provider || '')}</span>
            <span><strong>Model:</strong> ${esc(run.model_name || '')}</span>
            <span><strong>Product:</strong> ${esc(run.product || run.product_name || '')}</span>
            <span><strong>Started:</strong> ${run.run_timestamp ? new Date(run.run_timestamp).toLocaleString() : '—'}</span>
            <span><strong>Run ID:</strong> <code>${esc(run.run_id || '')}</code></span>
        </div>`;

    // Steps timeline
    const stepsHtml = steps.length > 0
        ? `<div class="detail-steps">
            <h4>Attack Timeline (${steps.length} requests)</h4>
            <div class="steps-timeline">
                ${steps.map(s => {
                    const statusClass = `status-${Math.floor((s.status_code || 0) / 100)}xx`;
                    const isLoop = metrics.loops && metrics.loops.some(l =>
                        s.path === l.path && s.step_number >= l.start_step && s.step_number < l.start_step + l.count
                    );
                    const rowClass = isLoop ? 'step-row loop-step' : 'step-row';
                    return `<div class="${rowClass}">
                        <span class="step-num">#${s.step_number}</span>
                        <span class="step-method method-${(s.method || '').toLowerCase()}">${esc(s.method)}</span>
                        <span class="step-path">${esc(s.path)}${s.query_string ? '?' + esc(s.query_string) : ''}</span>
                        <span class="step-status ${statusClass}">${s.status_code || '?'}</span>
                        <span class="step-time">${s.duration_ms ? s.duration_ms.toFixed(0) + 'ms' : ''}</span>
                    </div>`;
                }).join('')}
            </div>
          </div>`
        : '<div class="no-steps">No HTTP steps recorded for this run.</div>';

    // Flag attempts
    const flagsHtml = flags.length > 0
        ? `<div class="detail-flags">
            <h4>Flag Attempts (${flags.length})</h4>
            ${flags.map(f => {
                const fClass = f.result === 'correct' ? 'flag-correct' : 'flag-incorrect';
                return `<div class="flag-row ${fClass}">
                    <span>#${f.attempt_number}</span>
                    <span class="flag-result">${f.result === 'correct' ? 'CORRECT' : 'INCORRECT'}</span>
                    <code class="flag-value">${esc(f.flag_submitted || '')}</code>
                    <span class="flag-time">${f.timestamp ? new Date(f.timestamp).toLocaleTimeString() : ''}</span>
                </div>`;
            }).join('')}
          </div>`
        : '';

    bodyEl.innerHTML = infoHtml + metricsHtml + loopHtml + stepsHtml + flagsHtml;
}

function closeRunDetail() {
    document.getElementById('run-detail-modal').style.display = 'none';
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
    if (e.target.id === 'run-detail-modal') closeRunDetail();
});

// Close modal on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeRunDetail();
});

// Make functions globally accessible
window.showRunDetail = showRunDetail;
window.closeRunDetail = closeRunDetail;
