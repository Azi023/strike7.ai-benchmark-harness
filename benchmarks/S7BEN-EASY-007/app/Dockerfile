FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ARG FLAG_SECRET
ENV FLAG_SECRET=${FLAG_SECRET:-strike7-logging-secret-key}

# Create log directory
RUN mkdir -p /var/log/app

EXPOSE 5000

CMD ["python", "app.py"]
