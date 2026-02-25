FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    flask==3.0.0 \
    pyjwt==2.8.0 \
    pyotp==2.9.0

# Copy application
COPY app.py .

# Expose port
EXPOSE 8090

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8090/health')" || exit 1

# Run application
CMD ["python", "app.py"]
