.PHONY: up down test
up:
	docker-compose up -d && sleep 5
down:
	docker-compose down
test:
	curl http://localhost:8110/health
