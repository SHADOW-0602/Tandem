FROM php:8.4-cli-alpine

# Install system dependencies & PostgreSQL dev libraries
RUN apk add --no-cache \
    postgresql-dev \
    curl \
    git \
    unzip \
    libzip-dev

# Install required PHP extensions
RUN docker-php-ext-install \
    pdo \
    pdo_pgsql \
    pgsql \
    zip \
    pcntl \
    bcmath

# Install Composer
COPY --from=composer:2.8 /usr/bin/composer /usr/bin/composer

WORKDIR /app

# Copy dependency files first for layer caching
COPY composer.json composer.lock* ./

# Install dependencies without dev packages
RUN composer install --no-dev --no-interaction --prefer-dist --optimize-autoloader --no-scripts

# Copy application source
COPY . .

# Finish composer post-autoload-dump
RUN composer dump-autoload --optimize

# Ensure storage & cache permissions
RUN chmod -R 777 storage bootstrap/cache

# Expose default HTTP port
EXPOSE 8000

# Start artisan server bound to container port (Render supplies PORT env var)
CMD sh -c "php artisan config:clear && php artisan route:clear && php artisan serve --host=0.0.0.0 --port=${PORT:-8000}"
