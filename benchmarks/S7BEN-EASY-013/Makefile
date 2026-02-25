.PHONY: up down test clean
up:
	docker-compose up -d && sleep 5
down:
	docker-compose down
test:
	@curl -f http://localhost:8101/health && echo ✓
clean:
	docker-compose down -v --rmi local
