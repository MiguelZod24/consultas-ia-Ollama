<?php
require_once __DIR__ . '/bd.php';

// Todas las respuestas de esta API son JSON
header('Content-Type: application/json; charset=utf-8');

/** Envía una respuesta JSON con su código HTTP y termina. */
function responder(int $codigo, array $datos): void
{
    http_response_code($codigo);
    echo json_encode($datos, JSON_UNESCAPED_UNICODE);
    exit;
}

// Según cómo llegue la petición, hacemos una cosa u otra
try {
    $bd = conectarBD();

    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
        listarConsultas($bd);
    } elseif ($_SERVER['REQUEST_METHOD'] === 'POST') {
        crearConsulta($bd);
    } else {
        responder(405, ['error' => 'Método no permitido']);
    }
} catch (Throwable $e) {
    error_log($e->getMessage());  // el detalle técnico va al registro, no al usuario
    responder(500, ['error' => 'Error interno del servidor']);
}

/**
 * Devuelve una página de consultas (opcionalmente filtrada por categoría)
 * y los contadores por categoría.
 */
function listarConsultas(PDO $bd): void
{
    $porPagina = 10;
    $pagina = max(1, (int) ($_GET['pagina'] ?? 1));
    $categoria = $_GET['categoria'] ?? '';

    // Filtro opcional, solo si es una categoría válida
    $filtro = '';
    $parametros = [];
    if (in_array($categoria, ['Soporte Técnico', 'Duda Comercial', 'Agradecimiento'], true)) {
        $filtro = 'WHERE categoria = ?';
        $parametros[] = $categoria;
    }

    // Cuántas hay en total (para saber cuántas páginas hay)
    $sql = $bd->prepare("SELECT COUNT(*) FROM consultas $filtro");
    $sql->execute($parametros);
    $total = (int) $sql->fetchColumn();

    // Solo las de la página pedida
    $desde = ($pagina - 1) * $porPagina;
    $sql = $bd->prepare("SELECT * FROM consultas $filtro ORDER BY fecha DESC, id DESC LIMIT $porPagina OFFSET $desde");
    $sql->execute($parametros);
    $consultas = $sql->fetchAll();

    // Contadores por categoría
    $contadores = $bd->query(
        'SELECT categoria, COUNT(*) FROM consultas WHERE categoria IS NOT NULL GROUP BY categoria'
    )->fetchAll(PDO::FETCH_KEY_PAIR);
    $contadores['Total'] = (int) $bd->query('SELECT COUNT(*) FROM consultas')->fetchColumn();

    responder(200, [
        'consultas' => $consultas,
        'pagina' => $pagina,
        'paginas' => max(1, (int) ceil($total / $porPagina)),
        'contadores' => $contadores,
    ]);
}

/**
 * Guarda una consulta nueva, la clasifica con la IA en ese momento
 * y devuelve cómo ha quedado.
 */
function crearConsulta(PDO $bd): void
{
    // 1. Leer y validar lo que envía la web
    $entrada = json_decode(file_get_contents('php://input'), true);
    $texto = trim($entrada['texto'] ?? '');

    if ($texto === '') {
        responder(422, ['error' => 'La consulta no puede estar vacía']);
    }
    if (mb_strlen($texto) > 2000) {
        responder(422, ['error' => 'La consulta no puede superar 2000 caracteres']);
    }

    // 2. Guardarla ya como 'pendiente': si la IA falla, no se pierde
    $sql = $bd->prepare('INSERT INTO consultas (texto) VALUES (?)');
    $sql->execute([$texto]);
    $id = (int) $bd->lastInsertId();

    // 3. Pedir la clasificación al servicio de IA
    $resultado = clasificarConIA($texto);

    // 4. Guardar el resultado
    if ($resultado === null) {
        $bd->prepare("UPDATE consultas SET estado = 'error' WHERE id = ?")->execute([$id]);
    } else {
        $bd->prepare(
            "UPDATE consultas
             SET categoria = ?, modelo = ?, tiempo_ms = ?, estado = 'clasificada'
             WHERE id = ?"
        )->execute([$resultado['categoria'], $resultado['modelo'], $resultado['tiempo_ms'], $id]);
    }

    // 5. Devolver la consulta tal como ha quedado guardada
    $sql = $bd->prepare('SELECT * FROM consultas WHERE id = ?');
    $sql->execute([$id]);
    responder(201, ['consulta' => $sql->fetch()]);
}

/** Llama al servicio de IA en Python. Devuelve null si no responde bien. */
function clasificarConIA(string $texto): ?array
{
    $contexto = stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => "Content-Type: application/json\r\n",
            'content' => json_encode(['texto' => $texto]),
            'timeout' => 130,         // algo más que el límite de Python (120 s)
            'ignore_errors' => true,  // leer la respuesta aunque sea un error
        ],
    ]);

    $respuesta = @file_get_contents(getenv('IA_URL') . '/clasificar', false, $contexto);
    if ($respuesta === false) {
        return null;
    }

    $datos = json_decode($respuesta, true);
    return isset($datos['categoria']) ? $datos : null;
}