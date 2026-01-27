.PHONY: build up down test clean logs exploit reset help

build:
	@echo "[*] Building SBEN-HARD-04 containers..."
	docker compose build

up: build
	@echo "[*] Starting SBEN-HARD-04..."
	docker compose up -d
	@sleep 5
	@echo "[✓] SBEN-HARD-04 is running at http://localhost"

down:
	@echo "[*] Stopping SBEN-HARD-04..."
	docker compose down

test:
	@echo "[*] Testing SBEN-HARD-04 health..."
	@curl -sf http://localhost/health || (echo "[✗] Service not responding" && exit 1)
	@echo "[✓] All services healthy"

clean: down
	docker compose down -v && docker system prune -f

logs:
	docker compose logs -f

exploit:
	@python3 exploit.py

reset:
	@curl -X POST http://localhost/reset

help:
	@echo "SBEN-HARD-04: Auth Bypass with Rate Limiting"
	@echo "  make up      - Start services"
	@echo "  make test    - Health checks"
	@echo "  make exploit - Run exploitation"
	@echo "  make down    - Stop services"
