FROM alpine:3.18

WORKDIR /data

# Create some dummy files
RUN echo "Database credentials: admin / SecurePass123!" > /data/db_config.txt
RUN echo "API Keys: sk-1234567890abcdef" > /data/api_keys.txt

# Copy and set entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Keep container running
ENTRYPOINT ["/entrypoint.sh"]
