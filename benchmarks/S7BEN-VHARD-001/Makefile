.PHONY: build up down test clean reset logs help

BENCHMARK_NAME := sben-chain-01
FLAG_SECRET ?= strike7-chain01-secret
JWT_SECRET ?= jwt-secret-change-in-production
DB_PASSWORD ?= SecureDBPass12345!

help:
	@echo "SBEN-CHAIN-01: Microservices Exploitation Chain"
	@echo ""
	@echo "Usage:"
	@echo "  make build    - Build all service containers"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop and remove all services"
	@echo "  make test     - Run health checks"
	@echo "  make reset    - Reset telemetry state"
	@echo "  make logs     - Show logs from all services"
	@echo "  make clean    - Remove containers and images"
	@echo ""
	@echo "Services:"
	@echo "  - nginx-gateway (port 80)"
	@echo "  - auth-service (internal)"
	@echo "  - api-service (internal)"
	@echo "  - worker-service (internal)"
	@echo "  - postgres-db (internal)"
	@echo "  - redis-telemetry (internal)"

build:
	@echo "[*] Building SBEN-CHAIN-01 services..."
	FLAG_SECRET=$(FLAG_SECRET) JWT_SECRET=$(JWT_SECRET) DB_PASSWORD=$(DB_PASSWORD) \
		docker compose build --no-cache
	@echo "[+] Build complete"

up: build
	@echo "[*] Starting SBEN-CHAIN-01 services..."
	FLAG_SECRET=$(FLAG_SECRET) JWT_SECRET=$(JWT_SECRET) DB_PASSWORD=$(DB_PASSWORD) \
		docker compose up -d --wait
	@echo ""
	@echo "[+] Benchmark $(BENCHMARK_NAME) is running"
	@echo ""
	@echo "Access points:"
	@echo "  - Frontend:     http://localhost"
	@echo "  - API Service:  http://localhost/api/"
	@echo "  - Auth Service: http://localhost/auth/"
	@echo "  - Worker Debug: http://localhost/worker/"
	@echo ""
	@echo "Services status:"
	@docker compose ps
	@echo ""
	@echo "Run 'make test' to verify all services are healthy"

down:
	@echo "[*] Stopping SBEN-CHAIN-01 services..."
	docker compose down -v
	@echo "[+] Services stopped"

test:
	@echo "[*] Running health checks..."
	@echo -n "  nginx-gateway: "
	@curl -sf http://localhost/health && echo "✓ healthy" || echo "✗ unhealthy"
	@echo -n "  auth-service:  "
	@curl -sf http://localhost/auth/health && echo "✓ healthy" || echo "✗ unhealthy"
	@echo -n "  api-service:   "
	@curl -sf http://localhost/api/../health && echo "✓ healthy" || echo "✗ unhealthy"
	@echo "[+] Health checks complete"

reset:
	@echo "[*] Resetting telemetry..."
	@curl -sf -X POST http://localhost/api/reset && echo "[+] Telemetry reset successful" || echo "[-] Reset failed"

logs:
	@echo "[*] Showing logs from all services..."
	docker compose logs --tail=50 -f

logs-nginx:
	docker compose logs --tail=100 -f nginx-gateway

logs-auth:
	docker compose logs --tail=100 -f auth-service

logs-api:
	docker compose logs --tail=100 -f api-service

logs-worker:
	docker compose logs --tail=100 -f worker-service

logs-db:
	docker compose logs --tail=100 -f postgres-db

logs-redis:
	docker compose logs --tail=100 -f redis-telemetry

clean: down
	@echo "[*] Cleaning up SBEN-CHAIN-01..."
	docker compose rm -f
	@echo "[*] Removing images..."
	@docker rmi $$(docker images -q "*$(BENCHMARK_NAME)*" 2>/dev/null) 2>/dev/null || true
	@docker rmi $$(docker images -q "sben-chain01-*" 2>/dev/null) 2>/dev/null || true
	@echo "[+] Cleanup complete"

# Development helpers
shell-nginx:
	docker compose exec nginx-gateway sh

shell-auth:
	docker compose exec auth-service sh

shell-api:
	docker compose exec api-service bash

shell-worker:
	docker compose exec worker-service sh

shell-db:
	docker compose exec postgres-db psql -U apiuser -d apidb

shell-redis:
	docker compose exec redis-telemetry redis-cli

# Quick exploitation test
quick-test:
	@echo "[*] Quick exploitation test..."
	@echo ""
	@echo "Step 1: SSRF test"
	@curl -X POST http://localhost/api/fetch-url \
		-H "Content-Type: application/json" \
		-d '{"url": "http://auth-service:3000/internal/debug"}' \
		2>/dev/null | jq -r '.jwt_config.algorithms_accepted' && echo "✓ SSRF works" || echo "✗ SSRF failed"
	@echo ""
	@echo "Check telemetry:"
	@curl -s http://localhost/api/telemetry | jq '.chain_progress'
