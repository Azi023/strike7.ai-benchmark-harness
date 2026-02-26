FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ARG FLAG_SECRET
ENV FLAG_SECRET=${FLAG_SECRET:-strike7-secret-key-for-flag-generation}

# Create data directory
RUN mkdir -p /app/data

EXPOSE 5000

CMD ["python", "app.py"]
