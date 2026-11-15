# Clasificador de consultas con IA

Sistema que recibe consultas de clientes, las clasifica con IA en el momento en que entran (**Soporte Técnico**, **Duda Comercial** o **Agradecimiento**) y las guarda en una base de datos. La IA funciona en local con **Ollama**.

## Instalación

**Requisitos:** [Docker Desktop](https://www.docker.com/products/docker-desktop/), unos 10 GB libres de disco y 8 GB de RAM.

```bash
git clone <URL-DEL-REPOSITORIO>
cd consultas-ia
docker compose up --build
```

Cuando termine, abre **http://localhost:8080**

- **La primera vez** se descargan unos 6 GB (imágenes de Docker y modelo de IA) y tarda varios minutos. La web no arranca hasta que el modelo está listo.
- **La primera consulta** tarda 10–20 s, porque Ollama carga el modelo en memoria. Las siguientes, 1–2 s.
- **Para parar:** `docker compose down`

No hace falta configurar nada ni ninguna clave de API.

## Cómo funciona

```
Navegador ──► PHP ──► guarda la consulta en MySQL como "pendiente"
               │
               └──► Servicio de IA (Python) ──► Ollama (llama3.2:3b)
               │                                     │
               ◄──────── categoría, modelo y tiempo ◄─┘
               │
               └──► actualiza la consulta en MySQL como "clasificada"
                    y devuelve el resultado al navegador
```

## Qué es Ollama

[Ollama](https://ollama.com) es una herramienta de código abierto para **descargar y ejecutar modelos de IA en el propio equipo**, sin depender de servicios en la nube. Funciona como un servidor local con una API: se le envía un texto con instrucciones y devuelve la respuesta del modelo.

En este proyecto, el servicio de IA (`servicio-ia/clasificador.py`) envía a Ollama las instrucciones con ejemplos y la consulta del cliente, y Ollama devuelve la categoría.

## Uso de Ollama en la industria

Su uso más habitual en empresas es **mantener los datos dentro de la organización**. Con una API externa (OpenAI, Anthropic, Gemini…), cada consulta se envía a servidores de terceros. Con Ollama, el modelo se ejecuta en un equipo propio y los datos no salen de él. Esto reduce riesgos de seguridad y facilita cumplir la protección de datos (RGPD).

Ollama es la herramienta de referencia para IA en local, prototipos y herramientas internas. Para producción con cientos de usuarios simultáneos, la industria suele usar servidores especializados como vLLM.

## Por qué elegí Ollama

El enunciado permitía usar una API externa o simular la respuesta:

| Opción | Problema |
|---|---|
| API externa | Quien lo pruebe necesita una clave y pagar, o yo compartir la mía. Los datos salen a un servidor externo |
| Respuesta simulada | No es IA real: falla en cuanto el mensaje es ambiguo |
| **Ollama** | **IA real, sin claves, sin coste y sin enviar datos fuera** |

Este proyecto es una demostración sin datos reales, pero en un sistema real de atención al cliente las consultas podrían incluir nombres, direcciones o números de pedido. Además, funciona sin internet una vez descargado el modelo.

## Por qué el modelo `llama3.2:3b`

- **Sigue bien las instrucciones**, que es lo que necesita una tarea de clasificación.
- **Pesa unos 2 GB** y funciona en un portátil normal, sin tarjeta gráfica.
- **No tiene "modo razonamiento"**: algunos modelos recientes "piensan en voz alta" antes de responder, lo que los hace más lentos sin aportar nada al clasificar.
- **Su resultado está medido** (ver la sección siguiente).

Para cambiar de modelo, basta con cambiar su nombre en `docker-compose.yml` (marcado con `← modelo`).

## Evaluación del modelo

Para no fiarme de unas pocas pruebas a mano, el proyecto incluye un script que **mide la precisión de la IA** con 40 consultas cuya respuesta correcta ya se conoce (`servicio-ia/consultas_prueba.json`). Incluye 11 casos difíciles: ironía, agradecimientos que plantean un problema, preguntas que en realidad son quejas…

```bash
docker compose exec servicio-ia python evaluar.py
```

**Resultado: 40 de 40 aciertos (100 %), con una media de 1,9 s por consulta.**

Es una muestra pequeña, así que no garantiza que nunca falle. Se puede ampliar añadiendo consultas al archivo JSON, y sirve para comprobar que un cambio en el prompt o en el modelo no empeora los resultados.