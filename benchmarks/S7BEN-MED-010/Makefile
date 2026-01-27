.PHONY: build up down test clean reset

BENCHMARK_NAME := sben-1000-01
FLAG_SECRET ?= strike7-ssrf-secret-key

build:
	docker compose build --build-arg FLAG_SECRET="$(FLAG_SECRET)"

up: build
	docker compose up -d --wait
	@echo "Benchmark $(BENCHMARK_NAME) is running at http://localhost:5000"

down:
	docker compose down -v

test:
	@curl -sf http://localhost:5000/health && echo "Health check passed"

reset:
	@curl -sf -X POST http://localhost:5000/reset && echo "State reset successful"

clean: down
	docker compose rm -f
	docker rmi $$(docker images -q "*$(BENCHMARK_NAME)*") 2>/dev/null || true

.PHONY: test-metadata
test-metadata:
	@echo "Testing metadata service from within app container..."
	@docker compose exec app curl -s http://metadata:8080/health | python3 -m json.tool
