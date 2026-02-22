FROM n8nio/n8n:1.120.0

USER root

# Install curl for health checks
RUN apk add --no-cache curl

# Create flag file with a build-time random token
RUN FLAG_TOKEN=$(head -c 8 /dev/urandom | od -An -tx1 | tr -d ' \n') && \
    echo "S7BEN{n8n_rce_${FLAG_TOKEN}" > /flag.txt && \
    echo -n "}" >> /flag.txt && \
    chmod 644 /flag.txt

# Copy custom entrypoint
COPY entrypoint.sh /custom-entrypoint.sh
RUN chmod +x /custom-entrypoint.sh

USER node

EXPOSE 5678

ENTRYPOINT ["/custom-entrypoint.sh"]
