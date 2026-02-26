FROM n8nio/n8n:1.120.0

USER root

# Install curl for health checks
RUN apk add --no-cache curl

# Create flag file writable by node user
RUN touch /flag.txt && chown node:node /flag.txt

# Copy custom entrypoint
COPY entrypoint.sh /custom-entrypoint.sh
RUN chmod +x /custom-entrypoint.sh

USER node

EXPOSE 5678

ENTRYPOINT ["/custom-entrypoint.sh"]
