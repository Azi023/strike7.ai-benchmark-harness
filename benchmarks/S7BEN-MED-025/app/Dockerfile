FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN pip install flask
RUN mkdir -p /opt/panlogs/tmp/device_telemetry/hour
WORKDIR /app
COPY app.py .
CMD python app.py
