<?php
/**
 * Devuelve una conexión a la base de datos MySQL.
 * Los datos de conexión vienen de la configuración de Docker,
 * así no hay contraseñas escritas en el código.
 */
function conectarBD(): PDO
{
    $host = getenv('DB_HOST');
    $nombre = getenv('DB_NOMBRE');
    $usuario = getenv('DB_USUARIO');
    $clave = getenv('DB_CLAVE');

    return new PDO(
        "mysql:host=$host;dbname=$nombre;charset=utf8mb4",
        $usuario,
        $clave,
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]
    );
}