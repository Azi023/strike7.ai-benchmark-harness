FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir flask==3.0.0
COPY provider.py .
EXPOSE 8092
HEALTHCHECK --interval=10s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8092/health')" || exit 1
CMD ["python", "provider.py"]
