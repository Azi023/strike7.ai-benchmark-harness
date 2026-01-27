# Strike7 Dashboard Guide

Complete guide to using the Strike7 Benchmark Dashboard for managing, filtering, and analyzing all 64 security benchmarks.

---

## 🎯 Overview

The Strike7 Dashboard provides a comprehensive web interface for:
- **Browse** all 64 benchmarks with advanced filtering
- **Visualize** statistics and coverage across OWASP Top 10
- **Monitor** benchmark status and telemetry
- **Analyze** difficulty distribution and category breakdowns

---

## 🚀 Quick Start

### 1. Start the Dashboard

```bash
# Method 1: Quick deployment script
./scripts/deploy-dashboard.sh

# Method 2: Manual start
cd dashboard
pip install -r requirements.txt
python3 app.py
```

### 2. Access the Dashboard

Open your browser to: **http://localhost:5500**

### 3. Explore Benchmarks

- Use the **sidebar filters** to narrow down benchmarks
- Click any **benchmark card** for detailed information
- Switch between **Grid** and **List** views
- View **Statistics** and **Visualizations** tabs

---

## 📊 Features

### 1. Benchmark Browser

**Filter by:**
- **Category**: EASY, MED, HARD, VHARD, CVE
- **OWASP Top 10**: A01 through A10
- **Difficulty**: 1-9 scale
- **Phase**: Development phase (1-6)
- **Search**: Find by name or ID

**Display Options:**
- Grid view (cards)
- List view (detailed rows)
- Sort by various criteria

### 2. Statistics Dashboard

**Category Distribution:**
- EASY: 9 benchmarks (14%)
- MED: 16 benchmarks (25%)
- HARD: 14 benchmarks (22%)
- VHARD: 14 benchmarks (22%)
- CVE: 11 benchmarks (17%)

**OWASP Coverage:**
- Visual breakdown of all OWASP Top 10 categories
- Benchmark counts per category
- Percentage coverage

**Difficulty Analysis:**
- Distribution across 1-9 difficulty scale
- Average difficulty by category
- Trend analysis

**CWE Mapping:**
- Top 10 most-covered CWE categories
- Comprehensive weakness enumeration

### 3. Interactive Visualizations

**Charts Available:**
1. **Category Pie Chart** - Visual distribution of benchmark types
2. **OWASP Bar Chart** - Coverage across OWASP Top 10
3. **Difficulty Line Chart** - Challenge distribution by difficulty
4. **Phase Bar Chart** - Benchmarks by development phase

All charts are:
- Interactive (hover for details)
- Responsive (mobile-friendly)
- Real-time updated
- Export-ready

---

## 🔌 API Reference

The dashboard exposes a RESTful API for programmatic access.

### Base URL
```
http://localhost:5500/api
```

### Endpoints

#### GET /api/benchmarks
Get all benchmarks with optional filtering.

**Parameters:**
- `category` - Filter by category (EASY, MED, HARD, VHARD, CVE)
- `owasp` - Filter by OWASP code (A01, A02, etc.)
- `difficulty` - Filter by difficulty level (1-9)
- `cwe` - Filter by CWE code
- `phase` - Filter by phase (1-6)
- `search` - Search in name/ID

**Example:**
```bash
# Get all HARD benchmarks
curl "http://localhost:5500/api/benchmarks?category=HARD"

# Get all SQL Injection challenges (A03)
curl "http://localhost:5500/api/benchmarks?owasp=A03"

# Get difficulty 9 challenges
curl "http://localhost:5500/api/benchmarks?difficulty=9"

# Search for authentication challenges
curl "http://localhost:5500/api/benchmarks?search=auth"
```

**Response:**
```json
{
  "total": 14,
  "benchmarks": [
    {
      "id": "S7BEN-HARD-001",
      "name": "SQL Injection + ModSecurity WAF",
      "category": "HARD",
      "owasp": "A03:2025 - Injection",
      "cwe": "CWE-89",
      "port": 8001,
      "difficulty": 7,
      "phase": 3
    }
  ]
}
```

#### GET /api/benchmarks/{id}
Get detailed information about a specific benchmark.

**Example:**
```bash
curl "http://localhost:5500/api/benchmarks/S7BEN-HARD-018"
```

**Response:**
```json
{
  "id": "S7BEN-HARD-018",
  "name": "Kubernetes RBAC Privilege Escalation",
  "category": "HARD",
  "owasp": "A05:2025 - Security Misconfiguration",
  "cwe": "CWE-269",
  "port": 8101,
  "difficulty": 7,
  "phase": 6,
  "flag_format": "S7BEN{k8s_rb4c_esc4lat10n_[dynamic]}"
}
```

#### GET /api/statistics
Get comprehensive statistics across all benchmarks.

**Example:**
```bash
curl "http://localhost:5500/api/statistics"
```

**Response:**
```json
{
  "total_benchmarks": 64,
  "by_category": {
    "EASY": 9,
    "MED": 16,
    "HARD": 14,
    "VHARD": 14,
    "CVE": 11
  },
  "by_owasp": {
    "A01": 13,
    "A03": 18,
    "A04": 7,
    ...
  },
  "by_difficulty": {
    "1": 1,
    "2": 6,
    ...
  },
  "by_cwe": [
    ["CWE-89", 5],
    ["CWE-79", 4],
    ...
  ],
  "by_phase": {
    "1": 9,
    "2": 12,
    ...
  },
  "multi_container_count": 14
}
```

#### GET /api/statistics/owasp
Get detailed OWASP Top 10 coverage analysis.

**Example:**
```bash
curl "http://localhost:5500/api/statistics/owasp"
```

**Response:**
```json
{
  "coverage": {
    "A01": {
      "name": "Broken Access Control",
      "count": 13,
      "percentage": 20.3
    },
    "A03": {
      "name": "Injection",
      "count": 18,
      "percentage": 28.1
    },
    ...
  },
  "total_categories": 10,
  "total_benchmarks": 64
}
```

#### GET /api/categories
Get category distribution with counts and percentages.

**Example:**
```bash
curl "http://localhost:5500/api/categories"
```

#### GET /api/benchmark/{id}/status
Check if a benchmark container is currently running.

**Example:**
```bash
curl "http://localhost:5500/api/benchmark/S7BEN-HARD-018/status"
```

**Response:**
```json
{
  "benchmark_id": "S7BEN-HARD-018",
  "running": true,
  "status": "Up 5 minutes",
  "port": 8101
}
```

#### GET /api/benchmark/{id}/telemetry
Get real-time telemetry data from a running benchmark.

**Example:**
```bash
curl "http://localhost:5500/api/benchmark/S7BEN-HARD-018/telemetry"
```

**Response:**
```json
{
  "start_time": 1706004123.45,
  "exploitation_attempts": 3,
  "flag_captured": false,
  "uptime_seconds": 305
}
```

#### GET /api/health
Health check endpoint for monitoring dashboard status.

**Example:**
```bash
curl "http://localhost:5500/api/health"
```

**Response:**
```json
{
  "status": "healthy",
  "benchmarks_loaded": 64,
  "timestamp": "2026-01-22T12:00:00"
}
```

#### POST /api/reload
Reload benchmarks from the YAML registry (admin only).

**Example:**
```bash
curl -X POST "http://localhost:5500/api/reload"
```

---

## 📖 Usage Examples

### Example 1: Find All Authentication Challenges

```bash
# Using API
curl "http://localhost:5500/api/benchmarks?search=auth"

# Or in the dashboard:
# 1. Enter "auth" in search box
# 2. Results filtered automatically
```

### Example 2: Get All VHARD Multi-Container Challenges

```bash
# Using API
curl "http://localhost:5500/api/benchmarks?category=VHARD" | jq '.benchmarks[] | select(.containers != null)'

# Or in the dashboard:
# 1. Select "VHARD" in Category filter
# 2. Look for benchmarks with container counts
```

### Example 3: Monitor Specific Benchmark

```bash
#!/bin/bash
# Monitor S7BEN-HARD-018 status

while true; do
  curl -s "http://localhost:5500/api/benchmark/S7BEN-HARD-018/status" | jq .
  sleep 5
done
```

### Example 4: Export Statistics to CSV

```bash
# Get statistics and convert to CSV
curl "http://localhost:5500/api/statistics" | \
  jq -r '.by_category | to_entries[] | [.key, .value] | @csv' > category_stats.csv
```

---

## 🎨 Customization

### Change Dashboard Port

Edit `dashboard/app.py`:
```python
app.run(host='0.0.0.0', port=5500, debug=True)
```

### Add Custom Filters

1. **Backend** (`dashboard/app.py`):
```python
@app.route('/api/benchmarks', methods=['GET'])
def get_benchmarks():
    # Add new filter parameter
    custom_filter = request.args.get('custom_filter')
    if custom_filter:
        benchmarks = [b for b in benchmarks if b.get('custom_field') == custom_filter]
```

2. **Frontend** (`dashboard/templates/index.html`):
```html
<div class="filter-group">
    <label>Custom Filter</label>
    <select id="custom-filter">
        <option value="">All</option>
        <option value="value1">Option 1</option>
    </select>
</div>
```

3. **JavaScript** (`dashboard/static/js/dashboard.js`):
```javascript
function applyFilters() {
    const customFilter = document.getElementById('custom-filter').value;
    // Add to filter logic
}
```

### Customize Theme

Edit `dashboard/static/css/dashboard.css`:
```css
:root {
    --primary-color: #2563eb;  /* Change to your color */
    --bg-color: #0f172a;       /* Change background */
    --text-primary: #f1f5f9;   /* Change text color */
}
```

---

## 🔧 Troubleshooting

### Dashboard Won't Start

**Problem:** Port 5500 already in use
```bash
# Find what's using the port
lsof -i :5500
# Kill the process or change dashboard port
```

**Problem:** Missing dependencies
```bash
# Reinstall dependencies
cd dashboard
pip install -r requirements.txt --force-reinstall
```

### Benchmarks Not Loading

**Problem:** YAML parse error
```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('dashboard/config/benchmarks.yaml'))"
```

**Problem:** File not found
```bash
# Check file exists
ls -la dashboard/config/benchmarks.yaml
```

### Charts Not Displaying

**Problem:** Chart.js not loading
- Check internet connection (CDN required)
- Check browser console for errors
- Try refreshing the page

**Problem:** No data
```bash
# Verify statistics endpoint
curl "http://localhost:5500/api/statistics"
```

---

## 🎯 Best Practices

### 1. Regular Updates
Reload benchmark data after adding new challenges:
```bash
curl -X POST "http://localhost:5500/api/reload"
```

### 2. Monitoring
Use the health endpoint for uptime monitoring:
```bash
# Add to monitoring system
curl -f "http://localhost:5500/api/health" || alert
```

### 3. Performance
For large datasets, use filtered queries:
```bash
# Good: Filtered query
curl "http://localhost:5500/api/benchmarks?category=EASY"

# Less efficient: Get all then filter client-side
curl "http://localhost:5500/api/benchmarks"
```

### 4. Backup
Regularly backup the benchmark registry:
```bash
cp dashboard/config/benchmarks.yaml dashboard/config/benchmarks.yaml.backup
```

---

## 📚 Additional Resources

- **Dashboard README**: `dashboard/README.md`
- **API Documentation**: This file
- **Benchmark Registry**: `dashboard/config/benchmarks.yaml`
- **Test Reports**: `test-results/`
- **Phase 6B Report**: `docs/PHASE6B_FINAL_TEST_REPORT.md`

---

## 🆘 Support

For issues or questions:
1. Check this guide
2. Review API documentation
3. Check browser console for errors
4. Verify benchmark registry is valid YAML
5. Test with `curl` commands from examples above

---

**Dashboard Version**: 1.0.0
**Last Updated**: 2026-01-22
**Total Benchmarks**: 64
**API Version**: v1
