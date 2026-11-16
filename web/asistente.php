<?php
/**
 * Pasarela del asistente: reenvía la pregunta al servicio de IA en Python
 * y va devolviendo la respuesta al navegador a trozos (streaming), a medida que llega.
 */

header('Content-Type: application/x-ndjson; charset=utf-8');
header('Cache-Control: no-cache');
header('X-Accel-Buffering: no');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['tipo' => 'error', 'mensaje' => 'Método no permitido']) . "\n";
    exit;
}

// Sin búferes: cada trozo se envía al navegador en cuanto llega
while (ob_get_level() > 0) {
    ob_end_flush();
}
set_time_limit(0);

$peticion = curl_init(getenv('IA_URL') . '/preguntar');
curl_setopt_array($peticion, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => file_get_contents('php://input'),  // Python valida el contenido
    CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
    CURLOPT_TIMEOUT => 240,
    CURLOPT_WRITEFUNCTION => function ($peticion, $trozo) {
        // Si Python responde con un error, no se reenvía su detalle técnico
        if (curl_getinfo($peticion, CURLINFO_HTTP_CODE) !== 200) {
            return strlen($trozo);
        }
        echo $trozo;
        flush();
        return strlen($trozo);
    },
]);

$ok = curl_exec($peticion);
$codigo = curl_getinfo($peticion, CURLINFO_HTTP_CODE);
curl_close($peticion);

if ($ok === false || $codigo !== 200) {
    echo json_encode(['tipo' => 'error', 'mensaje' => 'El asistente no está disponible ahora mismo.'], JSON_UNESCAPED_UNICODE) . "\n";
}