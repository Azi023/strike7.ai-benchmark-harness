.PHONY: up down test clean build logs

up:
	@echo "[+] Starting S7BEN-VHARD-012: OAuth State Confusion"
	docker-compose up --build -d
	@sleep 7
	@echo "[+] App: http://localhost:8091"
	@echo "[+] OAuth: http://localhost:8092"

down:
	docker-compose down

test:
	@curl -f http://localhost:8091/health > /dev/null 2>&1 && echo "[+] Health check passed" || exit 1

clean:
	docker-compose down -v --rmi local

build:
	docker-compose build

logs:
	docker-compose logs -f
