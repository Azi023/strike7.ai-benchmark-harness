.PHONY: build up down logs test reset clean shell

# Build the Docker image
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
	@echo "Running health check..."
	@curl -s http://localhost:5000/health | grep -q '"status":"ok"' && echo "Health check passed" || echo "Health check failed"

# Reset application state
reset:
	@echo "Resetting application state..."
	@curl -s -X POST http://localhost:5000/reset | head -c 100
	@echo ""

# Clean up Docker resources
clean:
	docker-compose down -v --rmi local
	rm -rf app/__pycache__ app/*.pyc

# Open shell in container
shell:
	docker-compose exec app sh

# Test exploitation flow
exploit-test:
	@echo "=== SBEN-300-T1 Exploitation Test ==="
	@echo ""
	@echo "1. Checking current packages..."
	@curl -s http://localhost:5000/packages | head -c 200
	@echo ""
	@echo ""
	@echo "2. Triggering build..."
	@curl -s -X POST http://localhost:5000/build | head -c 300
	@echo ""
	@echo ""
	@echo "3. Checking compromise..."
	@curl -s http://localhost:5000/api/check-compromise
	@echo ""
	@echo ""
	@echo "4. Verifying exploitation..."
	@curl -s http://localhost:5000/api/verify
	@echo ""
