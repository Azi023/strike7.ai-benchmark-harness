# Strike7 Security Benchmarks

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Benchmarks](https://img.shields.io/badge/benchmarks-64-green.svg)
![OWASP](https://img.shields.io/badge/OWASP-Top%2010-red.svg)
![Docker](https://img.shields.io/badge/docker-required-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)

> AI-powered penetration testing benchmark platform with 64 real-world security challenges covering OWASP Top 10 vulnerabilities.

---

## 🎯 Overview

Strike7 Benchmarks is a comprehensive security testing platform designed for evaluating AI agents' capabilities in identifying and exploiting web application vulnerabilities. Each benchmark is a self-contained Docker environment featuring realistic, intentionally vulnerable applications that mirror real-world security challenges.

### Why Strike7?

- **Realistic Scenarios**: 64 challenges based on actual OWASP Top 10 vulnerabilities and real CVEs
- **AI-First Design**: RESTful API and MCP server integration for seamless AI agent interaction
- **Isolated Environments**: Every benchmark runs in Docker containers with proper network segmentation
- **Progressive Difficulty**: Five difficulty levels from EASY to VERY HARD, plus real CVE reproductions
- **Production-Ready**: Comprehensive health checks, automated testing, and telemetry

---

## ✨ Features

- ✅ **64 Security Challenges** across 5 difficulty levels (EASY, MED, HARD, VHARD, CVE)
- ✅ **Complete OWASP Top 10 Coverage** - All vulnerability categories represented
- ✅ **Docker-Based Isolation** - Self-contained environments with one-command deployment
- ✅ **RESTful API** - Automated benchmark management and flag submission
- ✅ **MCP Server Integration** - Native support for Claude and other AI agents
- ✅ **Real CVE Reproductions** - 11 challenges based on actual CVEs from 2023-2025
- ✅ **Multi-Container Architectures** - Advanced challenges with 2-6 containers per benchmark
- ✅ **Dynamic Flag Generation** - Environment-based flags prevent solution leakage
- ✅ **Comprehensive Documentation** - Detailed guides for each benchmark

---

## 📊 Benchmark Categories

| Category | Count | Difficulty | OWASP Coverage |
|----------|-------|------------|----------------|
| **EASY** | 9 | Tier 1 | A01, A02, A04, A09 |
| **MEDIUM** | 16 | Tier 1-2 | A01, A03, A07, A08 |
| **HARD** | 14 | Tier 2 | A03, A05, A06, A08 |
| **VERY HARD** | 14 | Tier 2-3 | A01, A03, A06, A08, A10 |
| **CVE** | 11 | Tier 2-3 | Real-world vulnerabilities |
| **TOTAL** | **64** | — | **10/10 OWASP categories** |

### OWASP Top 10 Coverage

```
A01: Broken Access Control          █████████████░░░░░  13 benchmarks
A02: Cryptographic Failures          ███░░░░░░░░░░░░░░░   3 benchmarks
A03: Injection                       ████████████████░░  18 benchmarks
A04: Insecure Design                 ██░░░░░░░░░░░░░░░░   2 benchmarks
A05: Security Misconfiguration       ████░░░░░░░░░░░░░░   4 benchmarks
A06: Vulnerable Components           ████░░░░░░░░░░░░░░   4 benchmarks
A07: Authentication Failures         █████░░░░░░░░░░░░░   6 benchmarks
A08: Data Integrity Failures         ██████░░░░░░░░░░░░   7 benchmarks
A09: Logging Failures                ██░░░░░░░░░░░░░░░░   2 benchmarks
A10: SSRF                            █████░░░░░░░░░░░░░   5 benchmarks
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11 or higher
- curl (for testing)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd strike7-benchmarks

# Install dashboard dependencies (optional)
cd dashboard
pip install -r requirements.txt
```

### Run Your First Benchmark

```bash
# Navigate to any benchmark
cd benchmarks/S7BEN-EASY-001

# Start the environment
make up

# Check health
make test

# The benchmark is now running on http://localhost:5000
# See the benchmark's TESTING.md for exploitation guidance

# Stop when done
make down
```

### Start the Dashboard (Optional)

```bash
cd dashboard
python app.py
# Dashboard available at http://localhost:8888
```

---

## 🤖 MCP Server Integration

Strike7 includes a Model Context Protocol (MCP) server for seamless integration with AI agents like Claude.

### Quick Setup

```bash
# Start the MCP server
cd dashboard
python strike7_mcp_server.py
```

### Configuration

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "strike7": {
      "command": "python",
      "args": ["/path/to/strike7-benchmarks/dashboard/strike7_mcp_server.py"]
    }
  }
}
```

### MCP Capabilities

- 📋 List and filter benchmarks by difficulty/category
- ▶️ Start/stop benchmark containers
- 🚩 Submit flags for validation
- 📊 Track session progress
- ⚡ Automated health checks

**See [docs/MCP_QUICKSTART.md](docs/MCP_QUICKSTART.md) for detailed setup instructions.**

---

## 📚 API Reference

The Strike7 Dashboard provides a RESTful API for programmatic access:

### Core Endpoints

```bash
GET  /api/benchmarks              # List all benchmarks
GET  /api/benchmarks/{id}         # Get benchmark details
POST /api/benchmarks/{id}/start   # Start a benchmark
POST /api/benchmarks/{id}/stop    # Stop a benchmark
POST /api/submit-flag             # Submit a flag for validation
GET  /api/session/{id}            # Get session progress
```

**Full API documentation: [dashboard/API_DOCUMENTATION.md](dashboard/API_DOCUMENTATION.md)**

---

## 🏗️ Architecture

### Standard Benchmark Structure

```
benchmarks/S7BEN-XXX-NNN/
├── app/                    # Vulnerable application code
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── benchmark.yaml          # OWASP metadata & configuration
├── benchmark.json          # Structured metadata
├── docker-compose.yml      # Container orchestration
├── Makefile               # Build automation
├── README.md              # Overview
└── TESTING.md             # Detailed exploitation guide
```

### Multi-Container Benchmarks

Advanced challenges (VHARD/CVE) feature complex architectures:

- **Microservices**: 6 containers with network segmentation
- **Active Directory**: Domain controller, file server, workstation
- **Attack Chains**: 3-5 exploitation steps required
- **Polyglot Stacks**: Python, Node.js, Java, Go, PHP

---

## 🎓 Usage Scenarios

### For Security Researchers

Test exploitation techniques in isolated environments:

```bash
cd benchmarks/S7BEN-VHARD-001
make up
# Perform your security testing
make down
```

### For AI Agent Developers

Evaluate your AI agent's security capabilities:

```python
import requests

# Start a benchmark via API
response = requests.post("http://localhost:8888/api/benchmarks/S7BEN-EASY-001/start")

# Let your AI agent work...
flag = ai_agent.exploit("http://localhost:5000")

# Submit the flag
result = requests.post("http://localhost:8888/api/submit-flag", json={
    "benchmark_id": "S7BEN-EASY-001",
    "flag": flag
})
```

### For Training & Education

Hands-on security workshops:

```bash
# Run multiple benchmarks for a workshop
for benchmark in S7BEN-EASY-*; do
    cd $benchmark
    make up
    # Present the challenge
    make down
    cd ..
done
```

---

## 📖 Documentation

### Getting Started
- [Quick Start](QUICKSTART.md) - Fast testing guide
- [MCP Quickstart](docs/MCP_QUICKSTART.md) - AI agent integration
- [API Documentation](dashboard/API_DOCUMENTATION.md) - RESTful API reference

### Deployment
- [Deployment Guide](docs/DEPLOYMENT.md) - Local deployment
- [VPS Deployment](docs/MCP_VPS_DEPLOYMENT_GUIDE.md) - Production deployment on VPS

### Development
- [Dashboard Guide](docs/DASHBOARD_GUIDE.md) - Dashboard development
- [Metrics & Telemetry](docs/METRICS_TELEMETRY_GUIDE.md) - Telemetry implementation

### Per-Benchmark Documentation
Each benchmark includes:
- `README.md` - Overview and objectives
- `TESTING.md` - Detailed exploitation walkthrough with multiple methods

---

## 🛠️ Make Targets

Every benchmark supports standardized make commands:

```bash
make build    # Build Docker images
make up       # Start containers with health checks
make down     # Stop and remove containers
make test     # Run health check
make clean    # Remove all images and volumes
make logs     # View container logs
```

---

## 🤝 Contributing

We welcome contributions! To add a new benchmark:

1. Use an existing benchmark as a template
2. Follow the standard directory structure
3. Include comprehensive `TESTING.md` with multiple exploitation methods
4. Test thoroughly with `make up && make test`
5. Update `benchmark.yaml` with proper OWASP mappings

---

## ⚠️ Security Warning

**IMPORTANT: These benchmarks contain intentional security vulnerabilities.**

- ❌ **DO NOT** deploy to production environments
- ❌ **DO NOT** expose to public networks
- ❌ **DO NOT** use in production codebases
- ✅ **DO** use in isolated test environments only
- ✅ **DO** run inside Docker containers
- ✅ **DO** follow responsible disclosure for any findings

**Not responsible for misuse. For educational and research purposes only.**

---

## 📊 Project Statistics

- **Total Benchmarks**: 64
- **Total Containers**: 100+ across all benchmarks
- **OWASP Coverage**: 10/10 categories (100%)
- **Documentation**: 150+ pages across all guides
- **Lines of Code**: 20,000+ (vulnerable applications + infrastructure)
- **Technologies**: Python, Node.js, Java, Go, PHP, PostgreSQL, MongoDB, Redis, LDAP

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Strike7 AI Benchmarks

---

## 🙏 Acknowledgments

- **OWASP Top 10 2021** for vulnerability categorization
- **CWE Database** for vulnerability classification
- **CVE Program** for real-world vulnerability data
- **Security Community** for best practices and research

---

## 📞 Support & Community

- **Documentation**: See `docs/` directory for comprehensive guides
- **Issues**: Report bugs and request features via GitHub Issues
- **Benchmark Help**: Check individual `TESTING.md` files for detailed guidance

---

**Ready to test your security skills? Start with the [Quick Start](#-quick-start) guide!** 🚀
