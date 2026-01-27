FROM python:3.11-slim

WORKDIR /worker

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY tasks.py .
COPY entrypoint.sh /entrypoint.sh

# Create directories and make entrypoint executable
RUN mkdir -p /worker/data && chmod +x /entrypoint.sh

# Run Celery worker via entrypoint
ENTRYPOINT ["/entrypoint.sh"]
