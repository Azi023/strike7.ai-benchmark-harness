# Strike7 Benchmark Dashboard

A comprehensive web dashboard for managing, filtering, and visualizing all 64 Strike7 security benchmarks.

## Features

### 🎯 Benchmark Management
- **Complete Registry**: View all 64 benchmarks across 5 categories
- **Advanced Filtering**: Filter by category, OWASP, difficulty, CWE, phase
- **Real-time Search**: Search benchmarks by name or ID
- **Detailed Views**: Click any benchmark for complete details

### 📊 Statistics & Analytics
- **Category Distribution**: See breakdown by EASY/MED/HARD/VHARD/CVE
- **OWASP Coverage**: Track coverage across OWASP Top 10 categories
- **Difficulty Analysis**: Distribution of challenges by difficulty (1-9)
- **CWE Mapping**: Top 10 most-tested CWE categories
- **Phase Tracking**: Benchmarks organized by development phase

### 📈 Visualizations
- **Interactive Charts**: Category, OWASP, difficulty, and phase charts
- **Real-time Updates**: Live data from benchmark registry
- **Responsive Design**: Works on desktop, tablet, and mobile

### 🔍 Filtering Capabilities
- Filter by **Category** (EASY, MED, HARD, VHARD, CVE)
- Filter by **OWASP Top 10** (A01-A10)
- Filter by **Difficulty** (1-9 scale)
- Filter by **CWE** codes
- Filter by **Phase** (1-6)
- **Search** by benchmark name or ID

## Quick Start

### Installation

```bash
# Navigate to dashboard directory
cd dashboard

# Install dependencies
pip install -r requirements.txt
```

### Running the Dashboard

```bash
# Start the dashboard server
python app.py

# Or using Python 3 explicitly
python3 app.py
```

The dashboard will be available at: **http://localhost:5500**

## Architecture

### Backend (Flask API)
- **Framework**: Flask 3.0.0 with CORS support
- **Data Source**: `config/benchmarks.yaml` (64 benchmarks)
- **Port**: 5500

### Frontend
- **HTML5** with semantic markup
- **CSS3** with custom properties (dark theme)
- **Vanilla JavaScript** (no framework dependencies)
- **Chart.js** for visualizations

### API Endpoints

#### GET /api/benchmarks
Get all benchmarks with optional filtering

**Query Parameters:**
- `category`: Filter by category (EASY, MED, HARD, VHARD, CVE)
- `owasp`: Filter by OWASP code (A01, A02, etc.)
- `difficulty`: Filter by difficulty level (1-9)
- `cwe`: Filter by CWE code
- `phase`: Filter by phase (1-6)
- `search`: Search in name/ID

**Example:**
```bash
curl "http://localhost:5500/api/benchmarks?category=HARD&difficulty=7"
```

#### GET /api/benchmarks/<id>
Get a single benchmark by ID

**Example:**
```bash
curl "http://localhost:5500/api/benchmarks/S7BEN-HARD-018"
```

#### GET /api/statistics
Get aggregated statistics

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
  "by_owasp": {...},
  "by_difficulty": {...},
  "by_cwe": [...],
  "by_phase": {...}
}
```

#### GET /api/statistics/owasp
Get detailed OWASP Top 10 coverage

#### GET /api/categories
Get category counts and percentages

#### GET /api/benchmark/<id>/status
Check if a benchmark container is running

#### GET /api/benchmark/<id>/telemetry
Get telemetry data from a running benchmark

#### GET /api/health
Health check endpoint

#### POST /api/reload
Reload benchmarks from YAML file

---

### **NEW in Phase 6C: Container Control & Flag Submission**

#### POST /api/benchmark/<id>/start
Start a benchmark container

**Request Body:**
```json
{
  "force_stop_others": true,
  "timeout_minutes": 30
}
```

**Response:**
```json
{
  "status": "success",
  "benchmark_id": "S7BEN-HARD-018",
  "port": 8101,
  "started_at": "2026-01-22T12:00:00",
  "auto_stop_at": "2026-01-22T12:30:00"
}
```

#### POST /api/benchmark/<id>/stop
Stop a benchmark container

#### POST /api/benchmark/<id>/submit-flag
Submit a captured flag for validation

**Request Body:**
```json
{
  "flag": "S7BEN{captured_flag}",
  "session_id": "sess_abc123",
  "agent_id": "my-agent"
}
```

**Response:**
```json
{
  "status": "success",
  "correct": true,
  "attempts": 1,
  "time_to_capture": 45.2
}
```

#### GET /api/containers/status
Get status of all running containers and system resources

#### POST /api/containers/stop-all
Emergency stop all running containers

---

### **NEW in Phase 6C: Session Tracking**

#### POST /api/session/start
Start a new evaluation session

**Request Body:**
```json
{
  "agent_id": "my-agent",
  "settings": {
    "max_concurrent_containers": 1
  }
}
```

#### GET /api/session/<id>/progress
Get current session progress and statistics

#### POST /api/session/<id>/end
End an evaluation session

#### GET /api/sessions
Get all sessions (optionally filter to active only)

#### GET /api/leaderboard
Get leaderboard of top performing sessions

**See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.**

## Directory Structure

```
dashboard/
├── app.py                  # Flask backend API
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── config/
│   └── benchmarks.yaml    # Master benchmark registry (64 benchmarks)
├── static/
│   ├── css/
│   │   └── dashboard.css  # Dashboard styles
│   └── js/
│       └── dashboard.js   # Dashboard functionality
└── templates/
    └── index.html         # Main dashboard page
```

## Usage Examples

### Filter Benchmarks via API

```bash
# Get all VHARD benchmarks
curl "http://localhost:5500/api/benchmarks?category=VHARD"

# Get all SQL Injection benchmarks (A03)
curl "http://localhost:5500/api/benchmarks?owasp=A03"

# Get all difficulty 9 benchmarks
curl "http://localhost:5500/api/benchmarks?difficulty=9"

# Search for "auth" benchmarks
curl "http://localhost:5500/api/benchmarks?search=auth"
```

### Get Statistics

```bash
# Get overall statistics
curl "http://localhost:5500/api/statistics"

# Get OWASP coverage details
curl "http://localhost:5500/api/statistics/owasp"
```

### Check Benchmark Status

```bash
# Check if a benchmark is running
curl "http://localhost:5500/api/benchmark/S7BEN-HARD-018/status"
```

## Dashboard Features

### Main View (Benchmarks Tab)
- Grid or list view toggle
- Color-coded by category (green=EASY, blue=MED, orange=HARD, red=VHARD, purple=CVE)
- Difficulty bars showing relative challenge level
- Click any card for detailed information

### Statistics Tab
- Category distribution with counts and percentages
- OWASP Top 10 coverage breakdown
- Difficulty level distribution
- Top 10 CWE categories

### Visualizations Tab
- **Category Pie Chart**: Visual breakdown of benchmark categories
- **OWASP Bar Chart**: Coverage across OWASP Top 10
- **Difficulty Line Chart**: Distribution by difficulty level
- **Phase Bar Chart**: Benchmarks by development phase

## Configuration

### Changing the Port

Edit `app.py`:
```python
app.run(host='0.0.0.0', port=5500, debug=True)
```

### Adding Custom Filters

The filtering system is extensible. To add new filters:

1. Add filter UI in `templates/index.html`
2. Add filter logic in `static/js/dashboard.js` (applyFilters function)
3. Add API parameter handling in `app.py` (get_benchmarks function)

## Development

### Hot Reload

Flask runs in debug mode by default, so changes to `app.py` will auto-reload.

For frontend changes (HTML/CSS/JS), simply refresh the browser.

### Adding New Statistics

1. Add data processing in `app.py` (get_statistics function)
2. Add display logic in `static/js/dashboard.js` (displayStatistics function)
3. Add HTML structure in `templates/index.html`

## Troubleshooting

### Dashboard won't start
- Check if port 5500 is already in use
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version (3.8+)

### Benchmarks not loading
- Check if `config/benchmarks.yaml` exists and is valid YAML
- Try reloading: `curl -X POST http://localhost:5500/api/reload`

### Charts not displaying
- Ensure Chart.js CDN is accessible
- Check browser console for JavaScript errors

## Phase 6C: NEW API Features (2026-01-22) 🚀

### Container Management API
- ✅ **Start/Stop Containers**: Control benchmark containers via API
- ✅ **Container Status Monitoring**: Real-time container and system metrics
- ✅ **Single Container Mode**: Safety enforcement (only 1 at a time)
- ✅ **Auto-timeout**: Containers auto-stop after 30 minutes

### Flag Submission API
- ✅ **Flag Validation**: Submit and validate captured flags
- ✅ **Attempt Tracking**: Track submission attempts per session
- ✅ **Time-to-Capture**: Measure solve time from container start
- ✅ **Hints**: Automatic hints after 3 failed attempts

### Session Tracking API
- ✅ **Session Management**: Track AI agent progress across benchmarks
- ✅ **Progress Monitoring**: Real-time statistics and results
- ✅ **Leaderboard**: Rank agents by performance
- ✅ **Multi-session Support**: Handle multiple concurrent evaluations

### Safety Features
- ✅ **Safety Daemon**: Background process enforcing limits
- ✅ **Resource Monitoring**: CPU, memory, system health checks
- ✅ **Auto-cleanup**: Orphaned container detection and removal
- ✅ **Configurable Limits**: Customize via settings.yaml

### Python Client Library
- ✅ **Strike7Client**: High-level API wrapper for AI agents
- ✅ **Helper Methods**: Simplified workflows and error handling
- ✅ **Examples**: Complete usage examples and templates

**📚 Documentation:**
- [API Reference](API_DOCUMENTATION.md) - Complete API documentation
- [Quick Start Guide](QUICKSTART_API.md) - Get started in 5 minutes
- [Agent Client](agent_client.py) - Python client library

## Future Enhancements

- [ ] Live telemetry streaming
- [ ] User authentication and API keys
- [ ] Bookmark/favorite benchmarks
- [ ] Export statistics to PDF/CSV
- [ ] Webhooks and notifications
- [ ] Multi-container parallel execution

## Technologies Used

- **Backend**: Python 3.11, Flask 3.0.0
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Charts**: Chart.js 4.4.0
- **Data Format**: YAML
- **API**: RESTful JSON API

## License

Part of the Strike7 Security Benchmark Suite

## Support

For issues or questions:
1. Check this README
2. Review API documentation above
3. Check browser console for errors
4. Verify benchmark registry is up to date

---

**Version**: 1.0.0
**Last Updated**: 2026-01-22
**Total Benchmarks**: 64
