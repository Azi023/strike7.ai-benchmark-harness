.PHONY: build up down logs test reset clean shell

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	@echo "Running health check..."
	@curl -s http://localhost:5000/health | grep -q '"status":"ok"' && echo "Health check passed" || echo "Health check failed"

reset:
	@echo "Resetting application state..."
	@curl -s -X POST http://localhost:5000/reset | head -c 100
	@echo ""

clean:
	docker-compose down -v --rmi local
	rm -rf app/__pycache__

shell:
	docker-compose exec app sh

exploit-test:
	@echo "=== SBEN-1010-T1 Exploitation Test ==="
	@echo ""
	@echo "1. Triggering type error..."
	@curl -s "http://localhost:5000/user/abc" | head -c 300
	@echo ""
	@echo ""
	@echo "2. Triggering DB error..."
	@curl -s -X POST "http://localhost:5000/search" -d "query='; DROP TABLE users; --" | head -c 500
	@echo ""
