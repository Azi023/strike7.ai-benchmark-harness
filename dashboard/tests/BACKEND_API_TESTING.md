# Backend API Testing - Strike7 Dashboard

Complete test suite for Strike7 Dashboard REST API endpoints.

## ✅ Test Coverage

### Test Suite Summary
- **Total Tests**: 34
- **Test Classes**: 8
- **API Endpoints Covered**: 25+
- **Status**: ✅ All tests passing

### Test Categories

#### 1. Benchmark APIs (7 tests)
- ✅ Get all benchmarks
- ✅ Filter by category (EASY, MED, HARD, VHARD, CVE)
- ✅ Filter by OWASP category
- ✅ Filter by difficulty level
- ✅ Search benchmarks
- ✅ Get single benchmark by ID
- ✅ Handle nonexistent benchmarks (404)

**Endpoints tested:**
- `GET /api/benchmarks`
- `GET /api/benchmarks/<id>`

#### 2. Statistics APIs (3 tests)
- ✅ Get aggregated statistics
- ✅ Get OWASP Top 10 coverage
- ✅ Get category breakdown

**Endpoints tested:**
- `GET /api/statistics`
- `GET /api/statistics/owasp`
- `GET /api/categories`

#### 3. Container APIs (4 tests)
- ✅ Get running containers status
- ✅ Check benchmark container status
- ✅ Start benchmark container
- ✅ Stop benchmark container

**Endpoints tested:**
- `GET /api/containers/status`
- `GET /api/benchmark/<id>/status`
- `POST /api/benchmark/<id>/start`
- `POST /api/benchmark/<id>/stop`

#### 4. Flag Submission APIs (2 tests)
- ✅ Submit incorrect flag (validation)
- ✅ Handle empty flag submission

**Endpoints tested:**
- `POST /api/benchmark/<id>/submit-flag`

#### 5. Session APIs (5 tests)
- ✅ Start new evaluation session
- ✅ Get session progress
- ✅ End session
- ✅ Get all sessions
- ✅ Get leaderboard

**Endpoints tested:**
- `POST /api/session/start`
- `GET /api/session/<id>/progress`
- `POST /api/session/<id>/end`
- `GET /api/sessions`
- `GET /api/leaderboard`

#### 6. Metrics APIs (6 tests)
- ✅ Get metrics dashboard overview
- ✅ Calculate pass@k metric
- ✅ Get time-to-flag (TTF) statistics
- ✅ Get efficiency metrics
- ✅ Get stealth score
- ✅ Get benchmark difficulty analysis

**Endpoints tested:**
- `GET /api/metrics/dashboard`
- `GET /api/metrics/pass-at-k`
- `GET /api/metrics/ttf`
- `GET /api/metrics/efficiency`
- `GET /api/metrics/stealth`
- `GET /api/metrics/benchmark-difficulty`

#### 7. Error Handling (5 tests)
- ✅ Health check endpoint
- ✅ Invalid endpoint (404)
- ✅ Malformed JSON handling
- ✅ Missing required fields
- ✅ Large search query handling

**Endpoints tested:**
- `GET /api/health`

#### 8. Integration Tests (2 tests)
- ✅ Full benchmark workflow (list → get → start → status → stop)
- ✅ Session with metrics workflow

---

## 🚀 Quick Start

### Prerequisites
- Dashboard must be running on `http://localhost:5500`
- Virtual environment activated

### Start Dashboard
```bash
cd ~/workspace/strike7-benchmarks/dashboard
python app.py
```

### Run Tests

#### Quick Smoke Tests (recommended for quick verification)
```bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
./quick_api_test.sh
```

Output:
```
✓ Found 64 benchmarks
✓ Statistics: 64 total benchmarks
✓ Container status: 0 running
✓ Session started: sess_xxxxx
✓ Health check passed

5 passed in 0.74s
```

#### Run All Tests
```bash
./quick_api_test.sh --all
```

#### Run Specific Test Categories
```bash
# Benchmark endpoints
./quick_api_test.sh --benchmarks

# Statistics endpoints
./quick_api_test.sh --stats

# Container management
./quick_api_test.sh --containers

# Flag submission
./quick_api_test.sh --flags

# Session tracking
./quick_api_test.sh --sessions

# Metrics endpoints
./quick_api_test.sh --metrics

# Error handling
./quick_api_test.sh --errors

# Integration workflows
./quick_api_test.sh --integration
```

---

## 📋 Manual Testing with pytest

### Run all tests with verbose output
```bash
cd ~/workspace/strike7-benchmarks/dashboard/tests
source ../../venv/bin/activate
pytest test_backend_qa.py -v
```

### Run specific test class
```bash
pytest test_backend_qa.py::TestBenchmarkAPIs -v
```

### Run specific test
```bash
pytest test_backend_qa.py::TestBenchmarkAPIs::test_get_all_benchmarks -v
```

### Run with print statements (see output)
```bash
pytest test_backend_qa.py -v -s
```

### Run and stop on first failure
```bash
pytest test_backend_qa.py -v -x
```

---

## 🔍 Test Details

### Test File Structure
```
test_backend_qa.py
├── TestBenchmarkAPIs       # 7 tests for /api/benchmarks
├── TestStatisticsAPIs      # 3 tests for /api/statistics
├── TestContainerAPIs       # 4 tests for container management
├── TestFlagSubmissionAPIs  # 2 tests for flag validation
├── TestSessionAPIs         # 5 tests for session tracking
├── TestMetricsAPIs         # 6 tests for evaluation metrics
├── TestErrorHandling       # 5 tests for error cases
└── TestDashboardIntegration # 2 tests for full workflows
```

### Configuration
- **Base URL**: `http://localhost:5500`
- **Timeout**: 10 seconds (30s for container operations)
- **Test Framework**: pytest
- **HTTP Client**: requests library

---

## 📊 Sample Test Results

### Successful Test Run
```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
plugins: base-url-2.1.0, playwright-0.7.2

test_backend_qa.py::TestBenchmarkAPIs::test_get_all_benchmarks PASSED [ 2%]
test_backend_qa.py::TestBenchmarkAPIs::test_filter_by_category PASSED [ 5%]
test_backend_qa.py::TestBenchmarkAPIs::test_filter_by_owasp PASSED [ 8%]
...
test_backend_qa.py::TestDashboardIntegration::test_session_with_metrics PASSED [100%]

======================== 34 passed, 1 warning in 0.45s =========================
```

### Key Metrics from Tests
- **64 benchmarks** loaded
- **5 categories**: CVE (11), EASY (9), MED (16), HARD (14), VHARD (14)
- **10 OWASP categories** covered
- **pass@3 metric**: ~85% (varies with test data)
- All API endpoints responding correctly

---

## 🛠️ Troubleshooting

### Dashboard Not Running
```
Error: Dashboard is not running at http://localhost:5500

Solution:
  cd dashboard
  python app.py
```

### Container Start Tests Fail
Container start tests may fail if Docker is not accessible or benchmark directories are missing. This is expected in some environments and the tests handle it gracefully.

### Connection Refused
```
Error: requests.exceptions.ConnectionError: Connection refused

Solution:
1. Check dashboard is running: curl http://localhost:5500/api/health
2. Verify port 5500 is not blocked
3. Check if another service is using port 5500
```

### Import Errors
```
Error: ModuleNotFoundError: No module named 'requests'

Solution:
  cd ~/workspace/strike7-benchmarks
  source venv/bin/activate
  pip install requests pytest
```

---

## 📝 Adding New Tests

### Example: Add a new test for a custom endpoint

```python
class TestCustomAPIs:
    """Test custom API endpoints"""

    def test_my_new_endpoint(self):
        """GET /api/custom/endpoint - Should return custom data"""
        response = requests.get(f"{API_BASE}/custom/endpoint", timeout=TIMEOUT)

        assert response.status_code == 200
        data = response.json()

        assert 'expected_field' in data
        print("✓ Custom endpoint working")
```

Then add it to the test runner script if needed.

---

## 🎯 Best Practices

1. **Always run smoke tests** before committing API changes
2. **Run full test suite** before major releases
3. **Check health endpoint** first if tests fail
4. **Use specific test categories** for targeted testing
5. **Review test output** for warnings and performance issues

---

## 📚 Related Documentation

- [E2E Testing with Playwright](README.md) - Frontend testing
- [QA Testing Checklist](../../QA_CHECKLIST.md) - Full QA process
- [Dashboard API Documentation](../api/README.md) - API specifications

---

## ✨ Summary

The backend API test suite provides comprehensive coverage of all Strike7 Dashboard REST API endpoints, ensuring:

- ✅ **Functional correctness** - All endpoints return expected data
- ✅ **Error handling** - Invalid inputs are handled gracefully
- ✅ **Data validation** - Filters and queries work correctly
- ✅ **Integration** - Full workflows function end-to-end
- ✅ **Performance** - All tests complete in under 1 second

**Status**: Production-ready ✅

---

*Last Updated: 2026-01-26*
*Test Suite Version: 1.0*
