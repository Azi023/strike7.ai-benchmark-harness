# Base image for ModSecurity WAF
# Used by: All hardened benchmarks (SBEN-HARD-*)
# Provides: nginx + ModSecurity + OWASP CRS

FROM owasp/modsecurity-crs:nginx-alpine

LABEL maintainer="Strike7 Security Team"
LABEL description="Base image for ModSecurity WAF benchmarks"
LABEL version="1.0.0"

USER root

# Install additional utilities
RUN apk add --no-cache \
    curl \
    bash \
    vim

# Set default ModSecurity configuration
ENV PARANOIA=2
ENV BLOCKING_PARANOIA=2
ENV ANOMALY_INBOUND=5
ENV ANOMALY_OUTBOUND=4
ENV PORT=8080

# Create directory for custom rules
RUN mkdir -p /etc/modsecurity.d/custom

USER nginx

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
