.PHONY: up down test clean
up:
	docker-compose up --build -d && sleep 5
down:
	docker-compose down
test:
	@curl -f http://localhost:8093/health > /dev/null 2>&1 && echo "✓ Health check passed" || exit 1
clean:
	docker-compose down -v --rmi local
