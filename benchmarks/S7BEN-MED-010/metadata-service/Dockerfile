FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . .

# Accept build arg for flag secret
ARG FLAG_SECRET
ENV FLAG_SECRET=${FLAG_SECRET}

# Expose port
EXPOSE 8080

# Run application
CMD ["python", "app.py"]
