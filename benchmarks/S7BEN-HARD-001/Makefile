.PHONY: build up down test clean logs reset help

BENCHMARK_NAME := sben-hard-01
FLAG ?= SBEN{waf_bypass_sql_1nj3ct10n_abc123def456}

help:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║  SBEN-HARD-01: SQL Injection with ModSecurity WAF             ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Usage:"
	@echo "  make build       - Build Docker images"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make test        - Run health checks"
	@echo "  make clean       - Remove containers and images"
	@echo "  make logs        - Show logs from all services"
	@echo "  make logs-nginx  - Show nginx/ModSecurity logs"
	@echo "  make logs-flask  - Show Flask application logs"
	@echo "  make logs-mysql  - Show MySQL logs"
	@echo "  make reset       - Reset telemetry data"
	@echo "  make shell-flask - Open shell in Flask container"
	@echo "  make exploit     - Run automated exploit script"
	@echo ""
	@echo "Target: http://localhost"
	@echo "Flag format: SBEN{...}"

build:
	@echo "[+] Building Docker images..."
	FLAG="$(FLAG)" docker compose build --no-cache

up: build
	@echo "[+] Starting services..."
	FLAG="$(FLAG)" docker compose up -d --wait
	@echo ""
	@echo "✓ Services started successfully!"
	@echo ""
	@echo "  URL: http://localhost"
	@echo "  Telemetry: http://localhost/api/telemetry"
	@echo "  Verify: http://localhost/api/verify"
	@echo ""
	@make test

down:
	@echo "[+] Stopping services..."
	docker compose down -v

test:
	@echo "[+] Running health checks..."
	@sleep 2
	@curl -sf http://localhost/health > /dev/null && echo "  ✓ Nginx health check passed" || echo "  ✗ Nginx health check failed"
	@curl -sf http://localhost/ > /dev/null && echo "  ✓ Homepage accessible" || echo "  ✗ Homepage failed"
	@curl -sf http://localhost/products?sort=name > /dev/null && echo "  ✓ Products endpoint working" || echo "  ✗ Products endpoint failed"
	@curl -sf http://localhost/api/telemetry > /dev/null && echo "  ✓ Telemetry endpoint working" || echo "  ✗ Telemetry endpoint failed"
	@echo ""
	@echo "Ready for exploitation!"

clean: down
	@echo "[+] Cleaning up..."
	docker compose rm -f
	docker volume rm sben-hard-01_mysql-data 2>/dev/null || true
	docker rmi $$(docker images -q "*$(BENCHMARK_NAME)*") 2>/dev/null || true
	@echo "✓ Cleanup complete"

logs:
	docker compose logs --tail=100 -f

logs-nginx:
	docker compose logs --tail=100 -f nginx-modsec

logs-flask:
	docker compose logs --tail=100 -f flask-app

logs-mysql:
	docker compose logs --tail=100 -f mysql-db

reset:
	@echo "[+] Resetting telemetry..."
	@curl -sf -X POST http://localhost/reset
	@echo ""
	@echo "✓ Telemetry reset complete"

shell-flask:
	docker compose exec flask-app bash

shell-nginx:
	docker compose exec nginx-modsec sh

exploit:
	@echo "[+] Running automated exploit..."
	@python3 exploit.py
