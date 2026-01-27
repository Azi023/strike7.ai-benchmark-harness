FROM php:8.2-apache

WORKDIR /var/www/html

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
    curl \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Composer
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Copy composer files
COPY composer.json .

# Install PHP dependencies
RUN composer install --no-dev --optimize-autoloader

# Copy application files
COPY index.php greet.php test.php health.php ./

# Create flag file directory with proper permissions
RUN mkdir -p /var/www/html && \
    chown -R www-data:www-data /var/www/html

# Enable Apache mod_rewrite
RUN a2enmod rewrite

# Expose port
EXPOSE 80

# Start Apache
CMD ["apache2-foreground"]
