.PHONY: build up down logs test reset clean shell

# Build the Docker images
build:
	docker-compose build

# Start the services
up:
	docker-compose up -d

# Stop the services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Run health check test
test:
	@echo "Running health checks..."
	@curl -s http://localhost:5000/health | grep -q '"status":"ok"' && echo "App health check passed" || echo "App health check failed"
	@curl -s http://localhost:5001/health | grep -q '"status":"ok"' && echo "Registry health check passed" || echo "Registry health check failed"

# Reset application state
reset:
	@echo "Resetting application state..."
	@curl -s -X POST http://localhost:5000/reset | head -c 100
	@echo ""

# Clean up Docker resources
clean:
	docker-compose down -v --rmi local
	rm -rf app/__pycache__ mock-registry/__pycache__

# Open shell in app container
shell:
	docker-compose exec app sh

# Open shell in registry container
shell-registry:
	docker-compose exec mock-registry sh
