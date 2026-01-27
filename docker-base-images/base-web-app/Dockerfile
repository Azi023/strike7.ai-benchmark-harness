# Base image for Python/Node.js web applications
# Used by: Flask apps, Node.js apps, hardened benchmarks
# Provides: Python 3.11, Node.js 20, common web utilities

FROM python:3.11-slim

LABEL maintainer="Strike7 Security Team"
LABEL description="Base image for web application benchmarks"
LABEL version="1.0.0"

# Install Node.js 20 and common utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    netcat-openbsd \
    git \
    vim \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install common Python packages
RUN pip install --no-cache-dir \
    flask \
    gunicorn \
    requests \
    redis

# Install common Node.js packages globally
RUN npm install -g \
    express \
    dotenv

# Create common directories
RUN mkdir -p /app /var/log

WORKDIR /app

CMD ["bash"]
