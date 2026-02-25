FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN pip install flask
WORKDIR /app
COPY app.py .
CMD python app.py
