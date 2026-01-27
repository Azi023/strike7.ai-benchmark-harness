# Strike7 MCP Server - VPS Deployment Guide

## Overview

This guide explains how to deploy the Strike7 MCP server on a VPS and make it accessible to remote users.

## Quick Start

```bash
# 1. Install dependencies
pip install mcp requests --break-system-packages

# 2. Set API URL for VPS
export STRIKE7_API_URL=http://YOUR_VPS_IP:5500

# 3. Run MCP server
python dashboard/strike7_mcp_server.py
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         VPS Server                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Dashboard API   │◀───────▶│   MCP Server     │         │
│  │  (Flask)         │         │  (FastMCP)       │         │
│  │  Port: 5500      │         │  stdio transport │         │
│  └──────────────────┘         └──────────────────┘         │
│         │                              │                     │
│         ▼                              ▼                     │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │ Docker Containers │         │  AI Agents       │         │
│  │ (Benchmarks)      │         │  (Claude, etc.)  │         │
│  └──────────────────┘         └──────────────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### 1. Environment Variables

Create `.env` file in project root:

```bash
# Strike7 API URL
STRIKE7_API_URL=http://YOUR_VPS_IP:5500

# Or for localhost
STRIKE7_API_URL=http://localhost:5500

# Or for Docker internal networking
STRIKE7_API_URL=http://host.docker.internal:5500
```

### 2. Firewall Configuration

Ensure ports are open on your VPS:

```bash
# Allow dashboard API
sudo ufw allow 5500/tcp

# Allow benchmark containers (if direct access needed)
sudo ufw allow 5000:6000/tcp

# Check status
sudo ufw status
```

### 3. Dashboard Configuration

Edit `dashboard/app.py` to allow remote connections:

```python
if __name__ == '__main__':
    # For VPS deployment
    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=5500,
        debug=False  # Disable debug in production
    )
```

Or use environment variable:

```bash
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5500
python dashboard/app.py
```

## Deployment Methods

### Method 1: Direct Execution

```bash
# Start dashboard
cd dashboard
python app.py &

# Start MCP server
export STRIKE7_API_URL=http://YOUR_VPS_IP:5500
python strike7_mcp_server.py
```

### Method 2: Systemd Service

Create `/etc/systemd/system/strike7-dashboard.service`:

```ini
[Unit]
Description=Strike7 Dashboard API
After=network.target docker.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/strike7-benchmarks/dashboard
Environment="FLASK_RUN_HOST=0.0.0.0"
Environment="FLASK_RUN_PORT=5500"
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

### Method 3: Docker Compose

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  dashboard:
    build:
      context: ./dashboard
      dockerfile: Dockerfile
    ports:
      - "5500:5500"
    volumes:
      - ./benchmarks:/app/benchmarks
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - FLASK_RUN_HOST=0.0.0.0
      - FLASK_RUN_PORT=5500
    restart: always

  mcp-server:
    build:
      context: ./dashboard
      dockerfile: Dockerfile.mcp
    environment:
      - STRIKE7_API_URL=http://dashboard:5500
    depends_on:
      - dashboard
    stdin_open: true
    tty: true
```

### Method 4: Nginx Reverse Proxy

For production, use Nginx:

```nginx
# /etc/nginx/sites-available/strike7
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5500;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/strike7 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Claude Desktop Integration

### Local Development

Edit `~/.config/claude/claude_desktop_config.json` (Linux/Mac) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "strike7": {
      "command": "python",
      "args": ["/absolute/path/to/strike7-benchmarks/dashboard/strike7_mcp_server.py"],
      "env": {
        "STRIKE7_API_URL": "http://localhost:5500"
      }
    }
  }
}
```

### Remote VPS Access

```json
{
  "mcpServers": {
    "strike7": {
      "command": "python",
      "args": ["/absolute/path/to/strike7-benchmarks/dashboard/strike7_mcp_server.py"],
      "env": {
        "STRIKE7_API_URL": "http://YOUR_VPS_IP:5500"
      }
    }
  }
}
```

### SSH Tunnel (Secure Remote Access)

If you don't want to expose port 5500 publicly:

```bash
# On your local machine
ssh -L 5500:localhost:5500 user@your-vps-ip

# Then use localhost in config
{
  "mcpServers": {
    "strike7": {
      "command": "python",
      "args": ["/absolute/path/to/strike7-benchmarks/dashboard/strike7_mcp_server.py"],
      "env": {
        "STRIKE7_API_URL": "http://localhost:5500"
      }
    }
  }
}
```

## Testing the Deployment

### 1. Test Dashboard API

```bash
# From VPS
curl http://localhost:5500/api/health

# From remote
curl http://YOUR_VPS_IP:5500/api/health
```

Expected response:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T...",
  "benchmarks_loaded": 64
}
```

### 2. Test MCP Server

Using MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python dashboard/strike7_mcp_server.py
```

This opens a browser interface to test all tools.

### 3. Test from Claude Desktop

1. Restart Claude Desktop
2. Open a new conversation
3. Try a command:

```
Use Strike7 MCP to list available benchmarks
```

Claude should be able to call the `list_benchmarks()` tool.

## Troubleshooting

### Issue: Connection Refused

**Cause:** Dashboard not running or firewall blocking

**Fix:**

```bash
# Check if dashboard is running
curl http://localhost:5500/api/health

# Check firewall
sudo ufw status

# Start dashboard
cd dashboard && python app.py
```

### Issue: Module Not Found

**Cause:** MCP SDK not installed

**Fix:**

```bash
pip install mcp requests --break-system-packages
```

### Issue: Permission Denied (Docker)

**Cause:** User not in docker group

**Fix:**

```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Issue: Timeout on Container Start

**Cause:** Docker pulling images or slow network

**Fix:**

```bash
# Pre-pull base images
docker pull python:3.11-slim
docker pull node:18-alpine

# Increase timeout in tool call
start_benchmark("S7BEN-EASY-001", timeout_minutes=60)
```

### Issue: MCP Server Not Responding

**Cause:** Wrong API URL or initialization issue

**Fix:**

```bash
# Check MCP server logs
python dashboard/strike7_mcp_server.py 2>&1 | tee mcp-debug.log

# Verify API URL
echo $STRIKE7_API_URL

# Test with correct URL
STRIKE7_API_URL=http://YOUR_VPS_IP:5500 python dashboard/strike7_mcp_server.py
```

## Security Considerations

### 1. API Authentication (TODO)

Currently the API has no authentication. For production:

```python
# Add API key authentication
from functools import wraps
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('STRIKE7_API_KEY'):
            return {'error': 'Unauthorized'}, 401
        return f(*args, **kwargs)
    return decorated
```

### 2. HTTPS/TLS

Use Nginx with Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. Rate Limiting

Add rate limiting to prevent abuse:

```bash
pip install flask-limiter
```

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per hour"]
)
```

### 4. Container Isolation

Ensure Docker containers can't access host:

```yaml
# In docker-compose.yml
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
```

## Performance Optimization

### 1. Use Gunicorn for Dashboard

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5500 app:app
```

### 2. Enable Response Caching

```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

@app.route('/api/benchmarks')
@cache.cached()
def get_benchmarks():
    # ...
```

### 3. Docker Image Caching

Keep frequently used images on VPS:

```bash
# Pre-pull all benchmark images
cd benchmarks
for dir in S7BEN-*/; do
  cd "$dir"
  docker compose pull
  cd ..
done
```

## Monitoring

### 1. Dashboard Health Endpoint

```bash
# Add to crontab for monitoring
*/5 * * * * curl -f http://localhost:5500/api/health || systemctl restart strike7-dashboard
```

### 2. Container Monitoring

```bash
# Check running containers
curl http://localhost:5500/api/containers/status

# Docker stats
docker stats --no-stream
```

### 3. Log Monitoring

```bash
# Dashboard logs
tail -f dashboard/logs/app.log

# MCP server logs
python dashboard/strike7_mcp_server.py 2>&1 | tee -a mcp-server.log
```

## Backup and Recovery

### 1. Backup Configuration

```bash
# Backup important files
tar -czf strike7-backup-$(date +%Y%m%d).tar.gz \
  dashboard/config/ \
  dashboard/data/ \
  .env \
  docker-compose.yml
```

### 2. Restore from Backup

```bash
tar -xzf strike7-backup-YYYYMMDD.tar.gz
```

## Scaling Considerations

For high traffic:

1. **Load Balancer**: Use multiple dashboard instances behind Nginx
2. **Database**: Move session data to Redis/PostgreSQL
3. **Container Orchestration**: Use Kubernetes for benchmark containers
4. **CDN**: Use Cloudflare for static assets

## Support

If you encounter issues:

1. Check logs: `dashboard/logs/` and MCP server stderr
2. Test API directly: `curl http://YOUR_VPS_IP:5500/api/health`
3. Verify firewall: `sudo ufw status`
4. Check Docker: `docker ps` and `docker logs`

## Summary

✅ **Local Development**: Use `STRIKE7_API_URL=http://localhost:5500`
✅ **VPS Deployment**: Use `STRIKE7_API_URL=http://YOUR_VPS_IP:5500`
✅ **SSH Tunnel**: Use `ssh -L 5500:localhost:5500` for secure access
✅ **Production**: Use Nginx + SSL + Systemd for stability

The MCP server will automatically detect the environment and configure appropriately!
