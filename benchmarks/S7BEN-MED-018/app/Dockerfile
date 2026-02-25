FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir flask==3.0.0
COPY app.py .
EXPOSE 8093
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8093/health')" || exit 1
CMD ["python", "app.py"]
