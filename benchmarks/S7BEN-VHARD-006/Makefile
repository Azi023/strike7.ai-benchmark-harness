.PHONY: help build up down test clean logs api db

help:
	@echo "SBEN-GQL-01: GraphQL Introspection to SQL Injection"
	@echo ""
	@echo "Available commands:"
	@echo "  make build    - Build all Docker containers"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make test     - Run health checks"
	@echo "  make clean    - Remove containers and volumes"
	@echo "  make logs     - View logs from all services"
	@echo "  make api      - Test GraphQL API endpoint"
	@echo "  make db       - Connect to PostgreSQL database"

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
	@echo "Testing GraphQL API health..."
	@curl -sf http://localhost:4000/health || echo "API health check failed"
	@echo ""
	@echo "Testing PostgreSQL connection..."
	@docker compose exec postgres-db pg_isready -U gqluser || echo "DB health check failed"

clean:
	docker compose down -v
	@echo "Cleaned up containers and volumes"

logs:
	docker compose logs -f

api:
	@echo "Testing GraphQL endpoint..."
	@curl http://localhost:4000/
	@echo ""
	@echo "\nTesting introspection query:"
	@curl -X POST http://localhost:4000/graphql \
		-H "Content-Type: application/json" \
		-d '{"query":"{ __schema { types { name } } }"}'

db:
	docker compose exec postgres-db psql -U gqluser -d gqldb
