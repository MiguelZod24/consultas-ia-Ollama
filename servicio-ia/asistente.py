"""
Asistente con RAG: responde preguntas sobre Ollama y sobre este proyecto
usando solo la documentación de la carpeta documentos/.
"""

import hashlib
import json
import math
import os
from pathlib import Path

import httpx

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODELO = os.environ.get("OLLAMA_MODELO", "llama3.2:3b")
OLLAMA_MODELO_EMBEDDINGS = os.environ.get("OLLAMA_MODELO_EMBEDDINGS", "qwen3-embedding:0.6b")

CARPETA_DOCUMENTOS = Path(__file__).with_name("documentos")
ARCHIVO_CACHE = Path(__file__).with_name("cache") / "embeddings.json"

TAMANO_MAXIMO_TROZO = 1000   # caracteres por trozo
TROZOS_DEL_PROYECTO = 2     # trozos del README que se pasan siempre al modelo
TROZOS_DE_OLLAMA = 3        # trozos de la documentación de Ollama
INSTRUCCION_BUSQUEDA = "Given a question, retrieve documentation passages that answer it"
MENSAJES_DE_HISTORIAL = 6    # últimas 3 preguntas y 3 respuestas

# Nombres legibles para mostrar las fuentes
NOMBRES_DOCUMENTOS = {
    "proyecto-README.md": "README del proyecto",
    "ollama-introduccion.md": "Ollama · Introducción",
    "ollama-quickstart.md": "Ollama · Quickstart",
    "ollama-faq.md": "Ollama · FAQ",
    "ollama-docker.md": "Ollama · Docker",
    "ollama-api.md": "Ollama · API",
}

PROMPT = """Eres el asistente de un proyecto de clasificación de consultas con IA que funciona con Ollama.
Responde SIEMPRE en español, de forma clara y breve (máximo 6 frases).
Usa SOLO la información de la DOCUMENTACIÓN de abajo, aunque esté en inglés.
Si la respuesta no está en la documentación, di exactamente: "No encuentro esa información en la documentación."
No inventes datos.

DOCUMENTACIÓN:
{documentacion}"""

# Aquí se guardan los trozos con sus embeddings una vez preparados
indice: list[dict] = []


# ---------------------------------------------------------------------------
# 1. Preparar el conocimiento: leer, trocear y calcular embeddings
# ---------------------------------------------------------------------------
def cortar_en_trozos(texto: str) -> list[str]:
    """Junta párrafos hasta llegar al tamaño máximo de trozo."""
    trozos, actual = [], ""
    for parrafo in texto.split("\n\n"):
        parrafo = parrafo.strip()
        if not parrafo or "llms.txt" in parrafo:   # quita el aviso de índice de la web de Ollama
            continue
        if actual and len(actual) + len(parrafo) > TAMANO_MAXIMO_TROZO:
            trozos.append(actual.strip())
            actual = ""
        actual += parrafo + "\n\n"
    if actual.strip():
        trozos.append(actual.strip())
    return trozos


def calcular_embeddings(textos: list[str]) -> list[list[float]]:
    """Pide a Ollama los embeddings, en grupos de 32 para no saturarlo."""
    vectores = []
    for i in range(0, len(textos), 32):
        respuesta = httpx.post(
            f"{OLLAMA_URL}/api/embed",
            json={"model": OLLAMA_MODELO_EMBEDDINGS, "input": textos[i:i + 32]},
            timeout=300,
        )
        respuesta.raise_for_status()
        vectores.extend(respuesta.json()["embeddings"])
    return vectores


def preparar_indice() -> None:
    """Carga los embeddings de la caché o, si los documentos han cambiado, los recalcula."""
    global indice

    trozos = []
    for archivo in sorted(CARPETA_DOCUMENTOS.glob("*.md")):
        for texto in cortar_en_trozos(archivo.read_text(encoding="utf-8")):
            trozos.append({"documento": archivo.name, "texto": texto})

    # "Huella" de los documentos y el modelo: si algo cambia, la caché deja de valer
    huella = hashlib.sha256(
        (OLLAMA_MODELO_EMBEDDINGS + json.dumps(trozos)).encode("utf-8")
    ).hexdigest()

    if ARCHIVO_CACHE.exists():
        cache = json.loads(ARCHIVO_CACHE.read_text(encoding="utf-8"))
        if cache.get("huella") == huella:
            indice = cache["trozos"]
            print(f"Asistente: {len(indice)} trozos cargados de la caché")
            return

    print(f"Asistente: calculando embeddings de {len(trozos)} trozos...")
    vectores = calcular_embeddings([t["texto"] for t in trozos])
    for trozo, vector in zip(trozos, vectores):
        trozo["vector"] = vector

    ARCHIVO_CACHE.parent.mkdir(exist_ok=True)
    ARCHIVO_CACHE.write_text(json.dumps({"huella": huella, "trozos": trozos}), encoding="utf-8")
    indice = trozos
    print("Asistente: embeddings calculados y guardados en caché")


# ---------------------------------------------------------------------------
# 2. Buscar los trozos más parecidos a la pregunta
# ---------------------------------------------------------------------------
def similitud_coseno(a: list[float], b: list[float]) -> float:
    """1 = mismo significado, 0 = nada que ver."""
    producto = sum(x * y for x, y in zip(a, b))
    normas = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return producto / normas if normas else 0.0


def buscar(texto: str) -> list[dict]:
    """Devuelve los trozos más parecidos: siempre algunos del proyecto y algunos de Ollama."""
    # Los modelos Qwen3-Embedding buscan mejor si la pregunta lleva esta instrucción delante
    consulta = f"Instruct: {INSTRUCCION_BUSQUEDA}\nQuery: {texto}"
    vector_pregunta = calcular_embeddings([consulta])[0]
    ordenados = sorted(indice, key=lambda t: similitud_coseno(vector_pregunta, t["vector"]), reverse=True)

    del_proyecto = [t for t in ordenados if t["documento"] == "proyecto-README.md"][:TROZOS_DEL_PROYECTO]
    de_ollama = [t for t in ordenados if t["documento"] != "proyecto-README.md"][:TROZOS_DE_OLLAMA]
    return del_proyecto + de_ollama


# ---------------------------------------------------------------------------
# 3. Responder con streaming: primero las fuentes, luego el texto a trozos
# ---------------------------------------------------------------------------
def responder(pregunta: str, historial: list[dict]):
    """Generador: va devolviendo eventos {"tipo": ...} a medida que se producen."""
    try:
        historial = historial[-MENSAJES_DE_HISTORIAL:]

        # Para buscar, se usa también la pregunta anterior ("¿Y es gratis?" sola no dice nada)
        anteriores = [m["contenido"] for m in historial if m["rol"] == "user"]
        texto_busqueda = f"{anteriores[-1]} {pregunta}" if anteriores else pregunta
        trozos = buscar(texto_busqueda)

        fuentes = list(dict.fromkeys(NOMBRES_DOCUMENTOS.get(t["documento"], t["documento"]) for t in trozos))
        yield {"tipo": "fuentes", "fuentes": fuentes}

        documentacion = "\n\n---\n\n".join(t["texto"] for t in trozos)
        mensajes = [{"role": "system", "content": PROMPT.format(documentacion=documentacion)}]
        mensajes += [{"role": m["rol"], "content": m["contenido"]} for m in historial]
        mensajes.append({"role": "user", "content": pregunta})

        with httpx.stream(
            "POST",
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODELO,
                "messages": mensajes,
                "options": {"temperature": 0},
                "stream": True,
            },
            timeout=180,
        ) as respuesta:
            respuesta.raise_for_status()
            for linea in respuesta.iter_lines():
                if not linea:
                    continue
                datos = json.loads(linea)
                texto = datos.get("message", {}).get("content", "")
                if texto:
                    yield {"tipo": "texto", "contenido": texto}
                if datos.get("done"):
                    break

        yield {"tipo": "fin"}
    except Exception as error:
        print(f"Asistente: error al responder: {error}")
        yield {"tipo": "error", "mensaje": "El asistente no ha podido responder. Inténtalo de nuevo."}
