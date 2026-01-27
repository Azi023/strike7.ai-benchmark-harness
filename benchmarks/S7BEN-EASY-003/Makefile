.PHONY: build up down test clean

BENCHMARK_NAME := sben-400-01
FLAG ?= SBEN{R4C3_C0ND1T10N_M4ST3R}

build:
	docker compose build --build-arg FLAG="$(FLAG)"

up: build
	docker compose up -d --wait
	@echo "Benchmark $(BENCHMARK_NAME) is running at http://localhost:5000"

down:
	docker compose down -v

test:
	@curl -sf http://localhost:5000/health && echo "Health check passed"

clean: down
	docker compose rm -f
	docker rmi $$(docker images -q "$(BENCHMARK_NAME)*") 2>/dev/null || true
