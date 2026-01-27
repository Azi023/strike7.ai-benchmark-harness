FROM alpine:3.18

WORKDIR /data

# Create flag file
ARG FLAG_VICTIM
RUN echo "${FLAG_VICTIM:-SBEN{victim_app_full_compromise_m3n4o5p6q7r8}}" > /data/admin_flag.txt

# Create some dummy files
RUN echo "Database credentials: admin / SecurePass123!" > /data/db_config.txt
RUN echo "API Keys: sk-1234567890abcdef" > /data/api_keys.txt

# Keep container running
CMD ["tail", "-f", "/dev/null"]
