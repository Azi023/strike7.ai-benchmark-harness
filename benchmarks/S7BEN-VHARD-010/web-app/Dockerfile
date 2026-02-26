FROM php:8.2-apache

WORKDIR /var/www/html

# Install dependencies
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Copy application files
COPY index.php health.php ./
COPY pages/ ./pages/

# Configure PHP session directory with proper permissions
RUN mkdir -p /var/lib/php/sessions && \
    chown -R www-data:www-data /var/lib/php/sessions && \
    chmod 777 /var/lib/php/sessions

# Make log directory accessible
RUN mkdir -p /var/log/apache2 && \
    chmod 755 /var/log/apache2

# Set proper permissions
RUN chown -R www-data:www-data /var/www/html

# Enable Apache modules
RUN a2enmod rewrite

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 80

# Use entrypoint for dynamic flag generation
ENTRYPOINT ["/entrypoint.sh"]
CMD ["apache2-foreground"]
