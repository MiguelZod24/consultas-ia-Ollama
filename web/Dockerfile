# Imagen oficial con PHP 8.3 y el servidor web Apache ya incluidos
FROM php:8.3-apache

# Extensión para que PHP pueda hablar con MySQL
RUN docker-php-ext-install pdo_mysql

# Copiamos la web a la carpeta que Apache publica
COPY . /var/www/html/