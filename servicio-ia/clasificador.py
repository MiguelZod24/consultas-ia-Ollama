import json
import os
import time

import httpx

# Las únicas categorías válidas
CATEGORIAS = ["Soporte Técnico", "Duda Comercial", "Agradecimiento"]

# Configuración: dónde está Ollama y qué modelo usar
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODELO = os.environ.get("OLLAMA_MODELO", "llama3.2:3b")

# Las instrucciones que se envían a la IA con CADA consulta
PROMPT = """Eres un clasificador de consultas de clientes de una empresa de logística.
Clasifica la consulta en UNA de estas categorías:
- "Soporte Técnico": problemas, incidencias, errores, retrasos, paquetes que no llegan o no se mueven, algo que no funciona.
- "Duda Comercial": preguntas sobre precios, tarifas, servicios, presupuestos, plazos o condiciones.
- "Agradecimiento": mensajes de gracias o valoraciones positivas SIN ningún problema pendiente.

Si un mensaje da las gracias pero también plantea un problema, es "Soporte Técnico".

Ejemplos:
"No puedo entrar en mi cuenta" -> Soporte Técnico
"¿Cuánto cuesta enviar a Italia?" -> Duda Comercial
"Gracias, todo llegó perfecto" -> Agradecimiento
"Gracias por responder, pero sigo sin recibir el pedido" -> Soporte Técnico

Responde SOLO con un JSON: {"categoria": "<categoría>"}"""

# Obliga a Ollama a responder con este formato exacto
ESQUEMA_RESPUESTA = {
    "type": "object",
    "properties": {
        "categoria": {"type": "string", "enum": CATEGORIAS},
    },
    "required": ["categoria"],
}


def clasificar(texto: str) -> dict:
    """Envía el texto a Ollama y devuelve la categoría, el modelo y el tiempo."""
    inicio = time.perf_counter()

    respuesta = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": OLLAMA_MODELO,
            "messages": [
                {"role": "system", "content": PROMPT},  # las instrucciones
                {"role": "user", "content": texto},     # la consulta del cliente
            ],
            "format": ESQUEMA_RESPUESTA,    # respuesta obligada a este formato
            "options": {"temperature": 0},  # sin "creatividad": siempre igual
            "stream": False,                # la respuesta entera de una vez
        },
        timeout=120,  # en un portátil sin tarjeta gráfica puede tardar
    )
    respuesta.raise_for_status()  # si Ollama da error, se para aquí

    contenido = respuesta.json()["message"]["content"]
    categoria = json.loads(contenido).get("categoria")

    # Nunca nos fiamos a ciegas de la IA: comprobamos lo que devuelve
    if categoria not in CATEGORIAS:
        raise ValueError(f"La IA devolvió una categoría no válida: {categoria}")

    tiempo_ms = int((time.perf_counter() - inicio) * 1000)
    return {"categoria": categoria, "modelo": OLLAMA_MODELO, "tiempo_ms": tiempo_ms}