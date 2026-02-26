FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ARG FLAG_SECRET
ENV FLAG_SECRET=${FLAG_SECRET:-strike7-toctou-secret-key}

# Create flag file with base content
RUN echo "FLAG_BASE_CONTENT_FOR_TOCTOU_EXPLOIT_VERIFICATION" > /flag.txt && \
    chmod 444 /flag.txt

# Create uploads directory
RUN mkdir -p /app/uploads

EXPOSE 5000

CMD ["python", "app.py"]
