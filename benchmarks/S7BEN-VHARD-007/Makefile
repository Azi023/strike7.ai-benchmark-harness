.PHONY: help build up down test clean logs

help:
	@echo "SBEN-XXE-01: XXE Out-of-Band Exfiltration"
	@echo ""
	@echo "  make build - Build containers"
	@echo "  make up    - Start services"
	@echo "  make down  - Stop services"
	@echo "  make test  - Health checks"
	@echo "  make clean - Remove volumes"
	@echo "  make logs  - View logs"

build:
	docker compose build

up:
	docker compose up -d
	@sleep 30
	@docker compose ps

down:
	docker compose down

test:
	@curl -sf http://localhost:8080/actuator/health || echo "Web-app failed"
	@curl -sf http://localhost:8888/health || echo "DTD server failed"

clean:
	docker compose down -v

logs:
	docker compose logs -f
