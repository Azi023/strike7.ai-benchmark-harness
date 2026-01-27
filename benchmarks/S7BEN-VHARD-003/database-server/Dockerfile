FROM postgres:15-alpine

# Install Kerberos client and tools
RUN apk add --no-cache \
    krb5 \
    krb5-dev \
    python3 \
    py3-pip \
    curl

# Install Flask for API
RUN pip3 install --break-system-packages flask psycopg2-binary

# Create app directory
RUN mkdir -p /opt/database

# Copy Kerberos config
COPY krb5.conf /etc/krb5.conf

# Copy application files
COPY app.py /opt/database/
COPY init-db.sql /docker-entrypoint-initdb.d/

# Copy startup script
COPY entrypoint.sh /opt/database/

RUN chmod +x /opt/database/*.sh

EXPOSE 5432 5000

WORKDIR /opt/database
