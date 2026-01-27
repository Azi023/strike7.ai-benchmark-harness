.PHONY: help build up down test clean logs webapp redis worker

help:
	@echo "SBEN-DESER-02: Python Pickle Deserialization Chain"
	@echo ""
	@echo "Available commands:"
	@echo "  make build    - Build all Docker containers"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make test     - Run health checks"
	@echo "  make clean    - Remove containers and volumes"
	@echo "  make logs     - View logs from all services"
	@echo "  make webapp   - Test web application endpoint"
	@echo "  make redis    - Connect to Redis CLI"
	@echo "  make worker   - View Celery worker logs"

build:
	docker compose build

up:
	docker compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 10
	@docker compose ps

down:
	docker compose down

test:
	@echo "Testing web-app health..."
	@curl -sf http://localhost:5000/health || echo "Web-app health check failed"
	@echo ""
	@echo "Testing Redis connection..."
	@docker compose exec redis-cache redis-cli ping || echo "Redis health check failed"
	@echo ""
	@echo "Testing Celery worker..."
	@docker compose exec worker-service celery -A tasks inspect ping || echo "Worker health check failed"

clean:
	docker compose down -v
	@echo "Cleaned up containers and volumes"

logs:
	docker compose logs -f

webapp:
	@echo "Testing web application..."
	@curl http://localhost:5000/
	@echo ""
	@echo "\nGetting session example:"
	@curl -s http://localhost:5000/api/session/example | python3 -m json.tool

redis:
	docker compose exec redis-cache redis-cli

worker:
	docker compose logs -f worker-service
