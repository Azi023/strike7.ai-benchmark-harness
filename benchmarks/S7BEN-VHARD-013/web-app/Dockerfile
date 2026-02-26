FROM php:8.2-apache

RUN apt-get update && apt-get install -y \
    curl \
    libcurl4-openssl-dev \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN a2enmod rewrite

COPY config/php.ini /usr/local/etc/php/conf.d/custom.ini
COPY config/000-default.conf /etc/apache2/sites-available/000-default.conf
COPY src/ /var/www/html/

RUN mkdir -p /var/www/html/uploads && chmod 777 /var/www/html/uploads

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
CMD ["apache2-foreground"]
