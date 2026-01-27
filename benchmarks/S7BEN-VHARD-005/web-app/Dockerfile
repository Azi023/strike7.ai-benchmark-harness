FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ templates/
COPY entrypoint.sh /entrypoint.sh

# Create directories and make entrypoint executable
RUN mkdir -p /app/data && chmod +x /entrypoint.sh

# Expose port
EXPOSE 5000

# Run application via entrypoint
ENTRYPOINT ["/entrypoint.sh"]
