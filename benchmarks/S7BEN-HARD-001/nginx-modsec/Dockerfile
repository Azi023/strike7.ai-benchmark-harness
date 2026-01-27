FROM owasp/modsecurity-crs:nginx-alpine

# The image uses templates and runs as non-root user
# Must use ports >= 1024

USER root

# Copy custom ModSecurity configuration
COPY modsec-config/custom.conf /etc/modsecurity.d/custom.conf
RUN chmod 644 /etc/modsecurity.d/custom.conf

# Set ModSecurity to blocking mode and paranoia level 2
ENV PARANOIA=2
ENV BLOCKING_PARANOIA=2
ENV ANOMALY_INBOUND=5
ENV ANOMALY_OUTBOUND=4

# Set backend configuration via environment variables
ENV BACKEND=http://flask-app:5000
ENV PORT=8080
ENV PROXY=1
ENV PROXY_LOCATION=/

USER nginx

EXPOSE 8080
