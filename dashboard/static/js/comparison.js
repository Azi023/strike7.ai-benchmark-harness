// ================================================================
// Strike7 Model Comparison Dashboard — JavaScript
// Vanilla JS, Chart.js 4.4.0, fetch() API
// ================================================================

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5500/api'
    : `${window.location.protocol}//${window.location.hostname}:5500/api`;

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

// ================================================================
// Init
// ================================================================

document.addEventListener('DOMContentLoaded', async () => {
    initTabs();
    initFilters();
    initSortHeaders();
    loadFiltersFromURL();
    await Promise.all([fetchEnums(), fetchCampaigns()]);
    await refreshAll();
});

async function refreshAll() {
    await Promise.all([
        fetchSummary(),
        fetchMatrix(),
        fetchModels(),
        fetchRecentRuns(),
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
    await Promise.all([fetchSummary(), fetchMatrix(), fetchRecentRuns()]);
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
// Leaderboard
// ================================================================

function buildLeaderboard() {
    // Aggregate summaryData by model_name
    const byModel = {};
    summaryData.forEach(s => {
        const key = s.model_name;
        if (!byModel[key]) {
            byModel[key] = {
                model_name: s.model_name,
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
        const m = byModel[key];
        m.total_runs += s.total_runs || 0;
        m.successful_runs += s.successful_runs || 0;
        if (s.avg_time_s != null) { m.time_sum += s.avg_time_s * s.total_runs; m.time_count += s.total_runs; }
        if (s.avg_tokens != null) { m.tokens_sum += s.avg_tokens * s.total_runs; m.tokens_count += s.total_runs; }
        if (s.avg_steps != null) { m.steps_sum += s.avg_steps * s.total_runs; m.steps_count += s.total_runs; }
        if (s.avg_cost_usd != null) { m.cost_sum += s.avg_cost_usd * s.total_runs; m.cost_count += s.total_runs; }
    });

    leaderboard = Object.values(byModel).map(m => ({
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

        const productTag = r.product_name && r.product_name !== r.model_name
            ? `<span class="product-label">${esc(r.product_name)}</span> `
            : '';

        return `<tr>
            <td class="mono-val" style="font-size:0.78rem;">${ts}</td>
            <td class="mono-val">${esc(r.benchmark_id)}</td>
            <td>${productTag}<span class="provider-badge ${providerClass}">${esc(r.provider)}</span> ${esc(r.model_name)}</td>
            <td>${result}</td>
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
