# Base image for databases
# Used by: Benchmarks requiring MySQL/PostgreSQL
# Provides: MySQL 8.0 with common configurations

FROM mysql:8.0

LABEL maintainer="Strike7 Security Team"
LABEL description="Base image for database benchmarks"
LABEL version="1.0.0"

# Note: MySQL 8.0 official image is minimal and doesn't need extra packages
# Benchmarks can extend this with specific requirements

# Set default MySQL configuration for development/testing
ENV MYSQL_ROOT_PASSWORD=rootpass123
ENV MYSQL_DATABASE=testdb
ENV MYSQL_USER=appuser
ENV MYSQL_PASSWORD=apppass123

# Copy custom MySQL configuration
COPY my.cnf /etc/mysql/conf.d/custom.cnf

EXPOSE 3306

CMD ["mysqld"]
