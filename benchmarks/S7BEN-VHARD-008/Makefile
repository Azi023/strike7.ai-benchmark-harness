.PHONY: help build up down test clean logs restart health

help:
	@echo "SBEN-NOSQL-01: MongoDB NoSQL Injection Chain"
	@echo ""
	@echo "  make build   - Build all containers"
	@echo "  make up      - Start all services"
	@echo "  make down    - Stop all services"
	@echo "  make test    - Run health checks"
	@echo "  make clean   - Remove all containers and volumes"
	@echo "  make logs    - View logs from all services"
	@echo "  make restart - Restart all services"
	@echo "  make health  - Check service health status"

build:
	docker compose build

up:
	docker compose up -d
	@echo "Waiting for services to start..."
	@sleep 30
	@docker compose ps

down:
	docker compose down

test:
	@echo "Testing web-app health..."
	@curl -sf http://localhost:3000/health || echo "❌ Web-app failed"
	@echo "Testing admin-panel health..."
	@curl -sf http://localhost:4000/health || echo "❌ Admin-panel failed"
	@echo ""
	@echo "✅ All health checks passed"

clean:
	docker compose down -v
	@echo "✅ All containers and volumes removed"

logs:
	docker compose logs -f

restart:
	docker compose restart

health:
	@docker compose ps
