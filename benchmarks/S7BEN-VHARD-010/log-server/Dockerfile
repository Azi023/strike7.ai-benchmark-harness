FROM php:8.2-apache

WORKDIR /var/www/html

# Install dependencies
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Copy application files
COPY index.php health.php ./

# Create and configure log directory
RUN mkdir -p /var/log/apache2 && \
    chmod 755 /var/log/apache2 && \
    touch /var/log/apache2/access.log && \
    chmod 644 /var/log/apache2/access.log

# Set proper permissions
RUN chown -R www-data:www-data /var/www/html /var/log/apache2

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 80

# Use entrypoint for dynamic flag generation
ENTRYPOINT ["/entrypoint.sh"]
CMD ["apache2-foreground"]
