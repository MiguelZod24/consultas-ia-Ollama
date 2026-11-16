# Clasificador de consultas con IA

Sistema que recibe consultas de clientes, las clasifica con IA en el momento en que entran (**Soporte Técnico**, **Duda Comercial** o **Agradecimiento**) y las guarda en una base de datos. Incluye además un **asistente** que responde preguntas sobre Ollama y sobre el propio proyecto. Toda la IA funciona en local con **Ollama**.

## Instalación

**Requisitos:** [Docker Desktop](https://www.docker.com/products/docker-desktop/), unos 10 GB libres de disco y 8 GB de RAM.

```bash
git clone https://github.com/MiguelZod24/consultas-ia-Ollama.git
cd consultas-ia-Ollama
docker compose up --build
```

Sin Git: en GitHub, botón **Code → Download ZIP**, descomprímelo y ejecuta `docker compose up --build` dentro de la carpeta.

Cuando termine, abre **http://localhost:8080**

- **La primera vez** se descargan unos 7 GB (imágenes de Docker y modelos de IA) y tarda varios minutos. La web no arranca hasta que los modelos están descargados y el asistente está preparado.
- **La primera consulta** tarda 10–20 s, porque Ollama carga el modelo en memoria. Las siguientes, 1–2 s.
- **Para parar:** `docker compose down`
- **Si va lento o alguna consulta queda en "Error al clasificar"**, suele ser falta de memoria: Docker Desktop usa por defecto la mitad de la RAM del equipo, y los modelos necesitan unos 4 GB libres.

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

Este proyecto es una demostración sin datos reales, pero en un sistema real de atención al cliente las consultas podrían incluir nombres, direcciones o números de pedido. Además, funciona sin internet una vez descargados los modelos.

## Por qué el modelo `llama3.2:3b`

- **Sigue bien las instrucciones**, que es lo que necesita una tarea de clasificación.
- **Pesa unos 2 GB** y funciona en un portátil normal, sin tarjeta gráfica.
- **No tiene "modo razonamiento"**: algunos modelos recientes "piensan en voz alta" antes de responder, lo que los hace más lentos sin aportar nada al clasificar.
- **Su resultado está medido** (ver la sección siguiente).

Para cambiar de modelo, basta con cambiar su nombre en los dos sitios de `docker-compose.yml` marcados con `←`: la lista de modelos que se descargan y `OLLAMA_MODELO`.

## Evaluación del modelo

Para no fiarme de unas pocas pruebas a mano, el proyecto incluye un script que **mide la precisión de la IA** con 40 consultas cuya respuesta correcta ya se conoce (`servicio-ia/consultas_prueba.json`). Incluye 11 casos difíciles: ironía, agradecimientos que plantean un problema, preguntas que en realidad son quejas…

```bash
docker compose exec servicio-ia python evaluar.py
```

**Resultado: 40 de 40 aciertos (100 %), con una media de 1,9 s por consulta.**

Es una muestra pequeña, así que no garantiza que nunca falle. Se puede ampliar añadiendo consultas al archivo JSON, y sirve para comprobar que un cambio en el prompt o en el modelo no empeora los resultados.

## Asistente sobre Ollama (RAG)

El botón 💬 de la esquina abre un chat que responde preguntas sobre Ollama y sobre este proyecto. Usa la técnica **RAG** (*Retrieval-Augmented Generation*): en lugar de responder "de memoria", el modelo busca primero en la documentación y responde **solo con lo que encuentra**. Si la respuesta no está, lo dice en vez de inventarla.

**Cómo funciona** (`servicio-ia/asistente.py`):
1. Al arrancar, los documentos de `servicio-ia/documentos/` (documentación oficial de Ollama y este README) se cortan en trozos y cada trozo se convierte en un **embedding** (un vector que representa su significado) con el modelo `qwen3-embedding:0.6b`. Se guardan en una caché para no recalcularlos en cada arranque.
2. Cuando llega una pregunta, se buscan por **similitud del coseno** los trozos más parecidos: siempre 2 del README del proyecto y 3 de la documentación de Ollama, para que ninguna de las dos fuentes quede fuera.
3. `llama3.2:3b` responde con esos trozos y la respuesta llega a la web **en streaming** (palabra a palabra) a través de PHP (`web/asistente.php`). Debajo de cada respuesta se muestran las fuentes usadas.

**Decisiones:**
- **Documentación en inglés, preguntas en español:** el modelo de embeddings es **multilingüe**, así que encuentra el texto correcto aunque esté en otro idioma, y el prompt le pide responder siempre en español.
- **Embeddings en memoria con caché en archivo**, sin base de datos de vectores: con unos 40 trozos, la búsqueda es instantánea. Con miles de documentos se usaría una base de datos de vectores (Qdrant, pgvector…).
- **Memoria de la conversación en el navegador:** se envían las últimas 3 preguntas y respuestas, y para buscar se usa también la pregunta anterior (así "¿Y es gratis?" se entiende en contexto). El servidor no guarda nada.
- **Seguridad:** el texto se muestra sin interpretarlo como HTML (contra XSS) y el historial solo admite mensajes de usuario y de asistente.

La primera pregunta tras arrancar tarda más, porque Ollama carga los modelos en memoria; también tras unos minutos sin uso, porque Ollama los descarga de la memoria.

La documentación de Ollama incluida procede de [docs.ollama.com](https://docs.ollama.com) (licencia MIT).
