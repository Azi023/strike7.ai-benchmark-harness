.PHONY: help build up down logs test clean

help:
	@echo "SBEN-DESER-01: Java Deserialization RCE"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make build   - Build all Docker containers"
	@echo "  make up      - Start all services"
	@echo "  make down    - Stop all services"
	@echo "  make restart - Restart all services"
	@echo "  make logs    - View all service logs"
	@echo "  make clean   - Remove all containers and volumes"
	@echo ""
	@echo "Testing Commands:"
	@echo "  make test    - Run basic connectivity tests"
	@echo "  make webapp  - Get web app info"
	@echo "  make session - Get sample serialized session"
	@echo ""
	@echo "Exploitation:"
	@echo "  Requires ysoserial: https://github.com/frohoff/ysoserial"
	@echo "  See TESTING.md for full exploitation walkthrough"

build:
	docker compose build

up:
	docker compose up -d
	@echo "Waiting for services to start..."
	@sleep 10
	@$(MAKE) test

down:
	docker compose down

restart:
	@$(MAKE) down
	@$(MAKE) up

logs:
	docker compose logs -f

clean:
	docker compose down -v

test:
	@echo "=== Testing Web App ==="
	@curl -s http://localhost:8080/health | grep -q healthy && echo "✓ Web App is healthy" || echo "✗ Web App failed"
	@echo ""
	@echo "=== Testing Internal API ==="
	@docker compose exec internal-api curl -s http://localhost:8081/health | grep -q healthy && echo "✓ Internal API is healthy" || echo "✗ Internal API failed"

webapp:
	@curl -s http://localhost:8080 | jq '.' || curl -s http://localhost:8080

session:
	@echo "=== Getting Sample Serialized Session ==="
	@curl -s http://localhost:8080/api/session | jq '.' || curl -s http://localhost:8080/api/session

login:
	@echo "=== Logging in as admin ==="
	@curl -s -X POST http://localhost:8080/login \
		-H "Content-Type: application/json" \
		-d '{"username":"admin","password":"admin123"}' | jq '.' || \
	curl -s -X POST http://localhost:8080/login \
		-H "Content-Type: application/json" \
		-d '{"username":"admin","password":"admin123"}'
