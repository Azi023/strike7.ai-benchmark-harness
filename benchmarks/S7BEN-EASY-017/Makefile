.PHONY: up down test clean build logs

up:
	@echo "[+] Starting S7BEN-EASY-017: 2FA Session State Bypass"
	docker-compose up --build -d
	@echo "[*] Waiting for service to be healthy..."
	@sleep 5
	@echo "[+] Benchmark running on http://localhost:8090"

down:
	@echo "[-] Stopping S7BEN-EASY-017"
	docker-compose down

test:
	@echo "[*] Running health check..."
	@curl -f http://localhost:8090/health > /dev/null 2>&1 && echo "[+] Health check passed" || (echo "[-] Health check failed" && exit 1)

clean:
	@echo "[*] Cleaning up containers and images..."
	docker-compose down -v --rmi local
	@echo "[+] Cleanup complete"

build:
	@echo "[*] Building containers..."
	docker-compose build

logs:
	docker-compose logs -f
