# Base image for Java vulnerability benchmarks
# Used by: Log4Shell, Text4Shell, Spring4Shell
# Provides: Java 11, Maven, common utilities

FROM maven:3.8-openjdk-11-slim

LABEL maintainer="Strike7 Security Team"
LABEL description="Base image for Java vulnerability benchmarks"
LABEL version="1.0.0"

# Install common utilities for Java vulnerability testing
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    netcat \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Create common directories
RUN mkdir -p /app /exploit /var/log

# Set working directory
WORKDIR /app

# Health check utility
COPY healthcheck.sh /usr/local/bin/healthcheck
RUN chmod +x /usr/local/bin/healthcheck

# Default command (should be overridden)
CMD ["bash"]
