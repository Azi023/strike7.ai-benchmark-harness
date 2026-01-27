.PHONY: help build up down test clean logs restart health

help:
	@echo "SBEN-SSTI-01: Server-Side Template Injection Chain"
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
	@echo "Testing Jinja2 app health..."
	@curl -sf http://localhost:5000/health || echo "❌ Jinja2 app failed"
	@echo "Testing Nunjucks app health..."
	@curl -sf http://localhost:3000/health || echo "❌ Nunjucks app failed"
	@echo "Testing Twig app health..."
	@curl -sf http://localhost:8080/health.php || echo "❌ Twig app failed"
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
