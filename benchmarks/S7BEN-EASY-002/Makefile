.PHONY: build up down test clean

BENCHMARK_NAME := sben-200-01
FLAG ?= SBEN{H4RDC0D3D_S3CR3TS_4R3_B4D}

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
