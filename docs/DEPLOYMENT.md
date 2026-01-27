# Strike7 Deployment Guide

Complete guide for deploying the Strike7 benchmark suite and dashboard in various environments.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Deployment](#local-deployment)
3. [Dashboard Deployment](#dashboard-deployment)
4. [Testing Infrastructure](#testing-infrastructure)
5. [Production Deployment](#production-deployment)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Docker** | 20.10+ | Container runtime |
| **docker-compose** | 2.0+ | Multi-container orchestration |
| **Python** | 3.8+ | Dashboard backend |
| **bash** | 4.0+ | Test scripts |
| **curl** | Any | API testing |
| **jq** | 1.6+ | JSON parsing in exploits |

### System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 20 GB free
- OS: Linux (Ubuntu 20.04+), macOS, Windows with WSL2

**Recommended:**
- CPU: 8+ cores
- RAM: 16+ GB
- Disk: 50+ GB free (for logs and test results)
- OS: Ubuntu 22.04 LTS

---

## Local Deployment

### 1. Clone Repository

```bash
git clone <repository-url>
cd strike7-benchmarks
```

### 2. Install Dependencies

**On Ubuntu/Debian:**
```bash
# Update package list
sudo apt-get update

# Install Docker
sudo apt-get install -y docker.io docker-compose

# Install Python dependencies
sudo apt-get install -y python3 python3-pip

# Install jq for JSON parsing
sudo apt-get install -y jq

# Add user to docker group (logout/login required)
sudo usermod -aG docker $USER
```

**On macOS:**
```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop
brew install --cask docker

# Install jq
brew install jq

# Install Python (if needed)
brew install python@3.11
```

**On Windows (WSL2):**
```bash
# Inside WSL2 Ubuntu
sudo apt-get update
sudo apt-get install -y docker.io docker-compose python3 python3-pip jq

# Start Docker service
sudo service docker start
```

### 3. Verify Installation

```bash
# Check Docker
docker --version
docker-compose --version

# Check Python
python3 --version
pip3 --version

# Check jq
jq --version

# Test Docker
docker run hello-world
```

---

## Dashboard Deployment

### Quick Start (Recommended)

```bash
# Make deploy script executable
chmod +x scripts/deploy-dashboard.sh

# Run deployment
./scripts/deploy-dashboard.sh
```

This will:
1. Check Python installation
2. Install dashboard dependencies
3. Verify benchmark registry
4. Start the dashboard on port 5500

### Manual Deployment

```bash
# Navigate to dashboard directory
cd dashboard

# Install Python dependencies
pip3 install -r requirements.txt

# Verify configuration
python3 -c "import yaml; print(yaml.safe_load(open('config/benchmarks.yaml'))['version'])"

# Start dashboard
python3 app.py
```

### Access Dashboard

Open browser to: **http://localhost:5500**

### Running as Background Service

**Using systemd (Linux):**

Create `/etc/systemd/system/strike7-dashboard.service`:
```ini
[Unit]
Description=Strike7 Benchmark Dashboard
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/strike7-benchmarks/dashboard
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable strike7-dashboard
sudo systemctl start strike7-dashboard
sudo systemctl status strike7-dashboard
```

**Using screen/tmux:**
```bash
# Using screen
screen -S strike7-dashboard
cd dashboard && python3 app.py
# Press Ctrl+A, D to detach

# Using tmux
tmux new -s strike7-dashboard
cd dashboard && python3 app.py
# Press Ctrl+B, D to detach
```

**Using nohup:**
```bash
cd dashboard
nohup python3 app.py > dashboard.log 2>&1 &
```

---

## Testing Infrastructure

### Run Comprehensive Tests

**Test all 64 benchmarks:**
```bash
# Make test script executable
chmod +x scripts/test-all-benchmarks.sh

# Run all tests
./scripts/test-all-benchmarks.sh
```

Results will be saved to `test-results/test-report-[timestamp].md`

### Test Specific Category

```bash
# Test only EASY benchmarks
for i in {001..009}; do
    cd benchmarks/S7BEN-EASY-$i
    docker-compose up -d
    sleep 5
    bash exploit.sh
    docker-compose down
    cd ../..
done
```

### Test Single Benchmark

```bash
cd benchmarks/S7BEN-HARD-018
docker-compose up -d
sleep 8
bash exploit.sh
docker-compose down
```

### Automated Testing Schedule

**Setup cron for daily tests:**
```bash
# Edit crontab
crontab -e

# Add line for daily 2 AM test
0 2 * * * cd /path/to/strike7-benchmarks && ./scripts/test-all-benchmarks.sh >> logs/daily-test.log 2>&1
```

---

## Production Deployment

### Security Hardening

**1. Change Default Ports**

Edit `dashboard/app.py`:
```python
app.run(host='0.0.0.0', port=8080, debug=False)
```

**2. Add Authentication**

Install Flask-Login:
```bash
pip3 install Flask-Login
```

Add to `dashboard/app.py`:
```python
from flask_login import LoginManager, login_required

login_manager = LoginManager()
login_manager.init_app(app)

@app.route('/api/benchmarks')
@login_required
def get_benchmarks():
    # ... existing code
```

**3. Enable HTTPS**

Use nginx as reverse proxy:
```nginx
server {
    listen 443 ssl;
    server_name benchmarks.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5500;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**4. Firewall Configuration**

```bash
# Allow only dashboard port
sudo ufw allow 5500/tcp

# Block direct benchmark ports (allow only from localhost)
sudo ufw deny 5000:8110/tcp

# Enable firewall
sudo ufw enable
```

### Performance Optimization

**1. Cache Benchmark Data**

Modify `dashboard/app.py` to cache more aggressively:
```python
from functools import lru_cache

@lru_cache(maxsize=1)
def load_benchmarks():
    # ... existing code
```

**2. Use Production WSGI Server**

Install gunicorn:
```bash
pip3 install gunicorn
```

Run with gunicorn:
```bash
cd dashboard
gunicorn -w 4 -b 0.0.0.0:5500 app:app
```

**3. Docker Compose for Dashboard**

Create `dashboard/docker-compose.yml`:
```yaml
version: '3.8'
services:
  dashboard:
    build: .
    ports:
      - "5500:5500"
    volumes:
      - ./config:/app/config
    restart: always
```

Create `dashboard/Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5500", "app:app"]
```

### Monitoring & Logging

**1. Application Logging**

Add to `dashboard/app.py`:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dashboard.log'),
        logging.StreamHandler()
    ]
)
```

**2. Health Monitoring**

Setup monitoring with curl:
```bash
# Check every 5 minutes
*/5 * * * * curl -f http://localhost:5500/api/health || echo "Dashboard down!" | mail -s "Alert" admin@example.com
```

**3. Log Rotation**

Create `/etc/logrotate.d/strike7-dashboard`:
```
/path/to/strike7-benchmarks/dashboard/dashboard.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 youruser youruser
}
```

### Backup Strategy

**1. Backup Benchmark Registry**

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups/strike7"

mkdir -p $BACKUP_DIR
cp dashboard/config/benchmarks.yaml $BACKUP_DIR/benchmarks-$DATE.yaml
cp -r test-results $BACKUP_DIR/test-results-$DATE

# Keep last 30 days
find $BACKUP_DIR -mtime +30 -delete
```

**2. Automated Backups**

```bash
# Add to crontab
0 1 * * * /path/to/backup.sh
```

---

## Environment-Specific Deployments

### AWS EC2

**1. Launch EC2 Instance**
- AMI: Ubuntu 22.04 LTS
- Instance Type: t3.medium (minimum)
- Storage: 30 GB GP3
- Security Group: Allow ports 22, 5500

**2. Install Dependencies**
```bash
ssh -i key.pem ubuntu@<instance-ip>

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install dependencies
sudo apt-get install -y python3-pip jq git
```

**3. Deploy Strike7**
```bash
git clone <repo-url>
cd strike7-benchmarks
./scripts/deploy-dashboard.sh
```

**4. Access via Public IP**
- Navigate to `http://<instance-ip>:5500`

### Google Cloud Platform

**1. Create VM Instance**
```bash
gcloud compute instances create strike7-benchmarks \
    --zone=us-central1-a \
    --machine-type=n1-standard-2 \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=30GB
```

**2. SSH and Deploy**
```bash
gcloud compute ssh strike7-benchmarks

# Follow standard installation
sudo apt-get update
# ... continue with deployment
```

### Azure VM

Similar to AWS EC2 - use Ubuntu 22.04 image with appropriate size.

### Docker-only Environment

**Run dashboard in Docker:**
```bash
cd dashboard
docker build -t strike7-dashboard .
docker run -d -p 5500:5500 \
    -v $(pwd)/config:/app/config \
    --name strike7-dashboard \
    strike7-dashboard
```

---

## Troubleshooting

### Dashboard Issues

**Problem:** Port already in use
```bash
# Find process
lsof -i :5500
# Kill process
kill -9 <PID>
```

**Problem:** Can't load benchmarks
```bash
# Validate YAML
python3 -c "import yaml; yaml.safe_load(open('dashboard/config/benchmarks.yaml'))"

# Check file permissions
ls -la dashboard/config/benchmarks.yaml

# Reload benchmarks
curl -X POST http://localhost:5500/api/reload
```

### Docker Issues

**Problem:** Docker daemon not running
```bash
# Linux
sudo systemctl start docker
sudo systemctl enable docker

# WSL2
sudo service docker start
```

**Problem:** Permission denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again
```

**Problem:** Port conflicts
```bash
# Find what's using a port
docker ps
netstat -tuln | grep 8001

# Stop conflicting container
docker stop <container-id>
```

### Testing Issues

**Problem:** jq not found
```bash
# Install jq
sudo apt-get install -y jq   # Ubuntu/Debian
brew install jq              # macOS
```

**Problem:** Exploit scripts fail
```bash
# Make executable
chmod +x benchmarks/*/exploit.sh

# Check shebang
head -1 benchmarks/S7BEN-*/exploit.sh
```

---

## Maintenance

### Regular Tasks

**Daily:**
- Check dashboard health
- Review test results
- Monitor disk space

**Weekly:**
- Run full test suite
- Review logs
- Update dependencies

**Monthly:**
- Backup configurations
- Review and archive old test results
- Update documentation

### Update Procedure

**Update benchmarks:**
```bash
git pull origin main
cd dashboard
pip install -r requirements.txt --upgrade
curl -X POST http://localhost:5500/api/reload
```

**Update Docker images:**
```bash
docker-compose down
docker-compose pull
docker-compose up -d
```

---

## Quick Reference

### Start Dashboard
```bash
cd dashboard && python3 app.py
```

### Test All Benchmarks
```bash
./scripts/test-all-benchmarks.sh
```

### Check Dashboard Health
```bash
curl http://localhost:5500/api/health
```

### View Statistics
```bash
curl http://localhost:5500/api/statistics | jq
```

### Reload Benchmarks
```bash
curl -X POST http://localhost:5500/api/reload
```

---

**Last Updated:** 2026-01-22
**Total Benchmarks:** 64
**Dashboard Version:** 1.0.0
