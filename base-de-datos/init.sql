-- Para que las tildes (Técnico...) se guarden bien
SET NAMES utf8mb4;

-- Crear la base de datos
CREATE DATABASE IF NOT EXISTS consultas_ia
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE consultas_ia;

-- Crear la tabla de consultas
CREATE TABLE IF NOT EXISTS consultas (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    texto      TEXT NOT NULL,
    categoria  ENUM('Soporte Técnico', 'Duda Comercial', 'Agradecimiento') NULL,
    estado     ENUM('pendiente', 'clasificada', 'error') NOT NULL DEFAULT 'pendiente',
    fecha      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modelo     VARCHAR(100) NULL,
    tiempo_ms  INT NULL
);

-- Registros de prueba (sin modelo: escritos a mano)
INSERT INTO consultas (id, texto, categoria, estado, fecha, modelo, tiempo_ms) VALUES
(1, 'No puedo acceder a mi cuenta, me da error al iniciar sesión.', 'Soporte Técnico', 'clasificada', '2026-11-15 15:30:54', NULL, NULL),
(2, '¿Qué precio tiene el envío urgente a Portugal?', 'Duda Comercial', 'clasificada', '2026-11-15 15:30:54', NULL, NULL),
(3, 'Muchas gracias, el pedido llegó perfecto y antes de tiempo.', 'Agradecimiento', 'clasificada', '2026-11-15 15:30:54', NULL, NULL);

-- Consultas reales clasificadas por la IA (llama3.2:3b) durante el desarrollo
INSERT INTO consultas (id, texto, categoria, estado, fecha, modelo, tiempo_ms) VALUES
(4, 'No encuentro mi paquete', 'Soporte Técnico', 'clasificada', '2026-11-15 15:39:30', 'llama3.2:3b', 17992),
(5, 'Cuantos dia tarda un paquete en llegar?', 'Duda Comercial', 'clasificada', '2026-11-15 15:40:36', 'llama3.2:3b', 1961),
(6, 'Cuanto cobran por enviar un paquete de 5 kg?', 'Duda Comercial', 'clasificada', '2026-11-15 15:41:22', 'llama3.2:3b', 1958),
(7, '¿Cuánto cuesta enviar un paquete de 10 kg a Francia?', 'Duda Comercial', 'clasificada', '2026-11-15 16:01:56', 'llama3.2:3b', 10025),
(8, '¿Hacéis entregas los sábados?', 'Duda Comercial', 'clasificada', '2026-11-15 16:02:24', 'llama3.2:3b', 1113),
(9, 'Mi pedido ha llegado a una dirección equivocada.', 'Soporte Técnico', 'clasificada', '2026-11-15 16:02:44', 'llama3.2:3b', 1293),
(10, 'He recibido la caja abierta y falta un producto.', 'Soporte Técnico', 'clasificada', '2026-11-15 16:03:00', 'llama3.2:3b', 1325),
(11, 'Quería felicitar al repartidor, fue muy amable y cuidadoso.', 'Agradecimiento', 'clasificada', '2026-11-15 16:03:16', 'llama3.2:3b', 1331),
(12, 'El paquete llegó impecable, gracias por el cuidado.', 'Agradecimiento', 'clasificada', '2026-11-15 16:03:34', 'llama3.2:3b', 1162),
(13, 'Todo perfecto con el último envío, ¡seguid así!', 'Agradecimiento', 'clasificada', '2026-11-15 16:03:51', 'llama3.2:3b', 1184),
(14, 'Gracias por contestar, pero sigo sin recibir mi pedido.', 'Soporte Técnico', 'clasificada', '2026-11-15 16:05:04', 'llama3.2:3b', 1334),
(15, 'El envío llegó bien, gracias. ¿Tenéis tarifas para envíos semanales?', 'Duda Comercial', 'clasificada', '2026-11-15 16:05:26', 'llama3.2:3b', 1359),
(16, 'Gracias de antemano, ¿hacéis envíos a Andorra?', 'Duda Comercial', 'clasificada', '2026-11-15 16:05:48', 'llama3.2:3b', 1306),
(17, 'Thank you, the delivery was perfect.', 'Agradecimiento', 'clasificada', '2026-11-15 16:06:03', 'llama3.2:3b', 1096),
(18, '¿Es normal que el seguimiento no se actualice desde ayer?', 'Soporte Técnico', 'clasificada', '2026-11-15 16:59:41', 'llama3.2:3b', 1709),
(19, 'Quiero cambiar la dirección de entrega de un pedido que ya está en camino.', 'Soporte Técnico', 'clasificada', '2026-11-15 17:00:07', 'llama3.2:3b', 1610),
(20, 'La etiqueta de envío se imprime cortada y no se lee el código de barras.', 'Soporte Técnico', 'clasificada', '2026-11-15 17:00:27', 'llama3.2:3b', 1589);