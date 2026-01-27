FROM php:8.2-apache

WORKDIR /var/www/html

# Install dependencies
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Copy application files
COPY index.php health.php ./
COPY pages/ ./pages/

# Create flag file
ARG FLAG_LFI=SBEN{lfi_path_traversal_file_read_a1b2c3}
ARG FLAG_SESSION=SBEN{php_session_poisoning_rce_g7h8i9}

RUN echo "$FLAG_LFI" > /var/www/html/flag.txt && \
    echo "$FLAG_SESSION" > /var/www/html/session_flag.txt

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

# Expose port
EXPOSE 80

# Start Apache
CMD ["apache2-foreground"]
