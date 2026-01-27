FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Create keys directory (app will populate it at runtime)
RUN mkdir -p keys

EXPOSE 5000

CMD ["python", "app.py"]
