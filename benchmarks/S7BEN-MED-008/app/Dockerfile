FROM n8nio/n8n:1.120.0

ARG FLAG=SBEN700_default_flag

USER root

# Install curl for health checks
RUN apk add --no-cache curl

# Create flag file (only readable by root, n8n runs as node)
RUN echo "SBEN{${FLAG}}" > /flag.txt && \
    chmod 644 /flag.txt

# Copy custom entrypoint
COPY entrypoint.sh /custom-entrypoint.sh
RUN chmod +x /custom-entrypoint.sh

USER node

EXPOSE 5678

ENTRYPOINT ["/custom-entrypoint.sh"]
