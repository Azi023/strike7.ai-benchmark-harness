FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy server script
COPY server.py .

# Create logs directory
RUN mkdir -p /logs

# Expose port
EXPOSE 8888

# Run server
CMD ["python", "server.py"]
