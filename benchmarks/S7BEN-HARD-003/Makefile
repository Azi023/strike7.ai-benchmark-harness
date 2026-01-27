.PHONY: build up down test clean logs logs-app logs-internal logs-metadata exploit reset help

# SBEN-HARD-03: SSRF with URL Filtering

build:
	@echo "[*] Building SBEN-HARD-03 containers..."
	docker compose build

up: build
	@echo "[*] Starting SBEN-HARD-03..."
	docker compose up -d
	@echo "[*] Waiting for services to be healthy..."
	@sleep 5
	@docker compose ps
	@echo ""
	@echo "[✓] SBEN-HARD-03 is running"
	@echo "    Web App:     http://localhost:5000"
	@echo "    Telemetry:   http://localhost:5000/api/telemetry"
	@echo "    Filters:     http://localhost:5000/debug/filters"

down:
	@echo "[*] Stopping SBEN-HARD-03..."
	docker compose down

test:
	@echo "[*] Testing SBEN-HARD-03 health..."
	@curl -sf http://localhost:5000/health || (echo "[✗] Web app not responding" && exit 1)
	@echo "[✓] Web app is healthy"
	@curl -sf http://localhost:5000/api/telemetry || (echo "[✗] Telemetry endpoint failed" && exit 1)
	@echo "[✓] Telemetry endpoint working"
	@echo "[✓] All services healthy"

clean: down
	@echo "[*] Cleaning up SBEN-HARD-03..."
	docker compose down -v
	docker system prune -f

logs:
	docker compose logs -f

logs-app:
	docker compose logs -f web-app

logs-internal:
	docker compose logs -f internal-api

logs-metadata:
	docker compose logs -f metadata-service

exploit:
	@echo "[*] Running automated SSRF exploitation..."
	@python3 exploit.py

reset:
	@echo "[*] Resetting benchmark state..."
	@curl -X POST http://localhost:5000/reset
	@echo "[✓] Benchmark reset complete"

help:
	@echo "SBEN-HARD-03: SSRF with URL Filtering"
	@echo ""
	@echo "Available targets:"
	@echo "  make build         - Build Docker containers"
	@echo "  make up            - Start all services"
	@echo "  make down          - Stop all services"
	@echo "  make test          - Run health checks"
	@echo "  make clean         - Clean up containers and volumes"
	@echo "  make logs          - Show all logs"
	@echo "  make logs-app      - Show web app logs"
	@echo "  make logs-internal - Show internal API logs"
	@echo "  make logs-metadata - Show metadata service logs"
	@echo "  make exploit       - Run automated exploitation"
	@echo "  make reset         - Reset benchmark state"
	@echo "  make help          - Show this help"
