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
	@curl -s -X POST http://localhost:5000/reset | head -c 100
	@echo ""

clean:
	docker-compose down -v --rmi local
	rm -rf app/__pycache__

shell:
	docker-compose exec app sh
