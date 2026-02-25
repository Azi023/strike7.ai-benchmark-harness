.PHONY: up down test clean
up:
	docker-compose up --build -d && sleep 5
down:
	docker-compose down
test:
	@curl -f http://localhost:8097/health && echo "✓"
clean:
	docker-compose down -v --rmi local
