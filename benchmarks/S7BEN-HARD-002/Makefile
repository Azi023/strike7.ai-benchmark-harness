.PHONY: build up down test clean logs logs-app logs-callback exploit reset help

# SBEN-HARD-02: XSS with Input Sanitization Bypass

build:
	@echo "[*] Building SBEN-HARD-02 containers..."
	docker compose build

up: build
	@echo "[*] Starting SBEN-HARD-02..."
	docker compose up -d
	@echo "[*] Waiting for services to be healthy..."
	@sleep 5
	@docker compose ps
	@echo ""
	@echo "[✓] SBEN-HARD-02 is running"
	@echo "    Web App:  http://localhost:3000"
	@echo "    Admin:    http://localhost:3000/admin"
	@echo "    Callback: http://localhost:3000/api/telemetry"

down:
	@echo "[*] Stopping SBEN-HARD-02..."
	docker compose down

test:
	@echo "[*] Testing SBEN-HARD-02 health..."
	@curl -sf http://localhost:3000/health || (echo "[✗] Web app not responding" && exit 1)
	@echo "[✓] Web app is healthy"
	@curl -sf http://localhost:3000/api/telemetry || (echo "[✗] Telemetry endpoint failed" && exit 1)
	@echo "[✓] Telemetry endpoint working"
	@echo "[✓] All services healthy"

clean: down
	@echo "[*] Cleaning up SBEN-HARD-02..."
	docker compose down -v
	docker system prune -f

logs:
	docker compose logs -f

logs-app:
	docker compose logs -f node-app

logs-callback:
	docker compose logs -f callback-server

exploit:
	@echo "[*] Running automated XSS exploitation..."
	@python3 exploit.py

reset:
	@echo "[*] Resetting benchmark state..."
	@curl -X POST http://localhost:3000/reset
	@curl -X POST http://localhost:8080/reset
	@echo "[✓] Benchmark reset complete"

help:
	@echo "SBEN-HARD-02: XSS with Input Sanitization Bypass"
	@echo ""
	@echo "Available targets:"
	@echo "  make build      - Build Docker containers"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make test       - Run health checks"
	@echo "  make clean      - Clean up containers and volumes"
	@echo "  make logs       - Show all logs"
	@echo "  make logs-app   - Show web app logs"
	@echo "  make logs-callback - Show callback server logs"
	@echo "  make exploit    - Run automated exploitation"
	@echo "  make reset      - Reset benchmark state"
	@echo "  make help       - Show this help"
