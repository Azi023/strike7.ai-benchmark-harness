FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ARG FLAG
ENV FLAG=${FLAG:-SBEN{DEFAULT_FLAG}}

EXPOSE 5000

# Run with Gunicorn, using 4 workers to enable concurrency (essential for race conditions)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
