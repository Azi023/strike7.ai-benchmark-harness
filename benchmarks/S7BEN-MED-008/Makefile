.PHONY: build up down clean test help

FLAG ?= $(shell openssl rand -hex 16)

help:
	@echo "SBEN-700-25: n8n RCE (CVE-2025-68613)"
	@echo ""
	@echo "Usage:"
	@echo "  make build [FLAG=yourflag]  - Build the benchmark"
	@echo "  make up [FLAG=yourflag]     - Start the benchmark"
	@echo "  make down                   - Stop the benchmark"
	@echo "  make clean                  - Remove all containers/images"
	@echo "  make test                   - Verify benchmark is working"
	@echo "  make logs                   - View container logs"

build:
	@echo "Building SBEN-700-25 with FLAG=$(FLAG)"
	FLAG=$(FLAG) docker compose build

up: build
	@echo "Starting n8n benchmark..."
	FLAG=$(FLAG) docker compose up -d --wait
	@echo "n8n available at http://localhost:5678"
	@echo "Credentials: admin@strike7.local / Strike7Demo!"

down:
	docker compose down

clean: down
	docker compose down -v --rmi local 2>/dev/null || true

test:
	@echo "Testing benchmark health..."
	@curl -sf http://localhost:5678/healthz && echo "✓ Health check passed" || echo "✗ Health check failed"

logs:
	docker compose logs -f
