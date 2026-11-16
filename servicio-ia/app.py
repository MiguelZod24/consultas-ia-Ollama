import json
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import asistente
import clasificador


@asynccontextmanager
async def al_arrancar(app: FastAPI):
    # Prepara el conocimiento del asistente antes de aceptar peticiones
    asistente.preparar_indice()
    yield


app = FastAPI(title="Servicio de IA - Clasificador y asistente", lifespan=al_arrancar)


# Cómo tiene que ser lo que nos envía PHP
class Consulta(BaseModel):
    texto: str = Field(min_length=1, max_length=2000)


class Mensaje(BaseModel):
    rol: Literal["user", "assistant"]
    contenido: str = Field(max_length=4000)


class Pregunta(BaseModel):
    pregunta: str = Field(min_length=1, max_length=500)
    historial: list[Mensaje] = []


@app.post("/clasificar")
def clasificar(consulta: Consulta):
    """PHP llama aquí con {"texto": "..."} y recibe la clasificación."""
    try:
        return clasificador.clasificar(consulta.texto)
    except Exception as error:
        # Si la IA falla, avisamos a PHP con un error claro
        raise HTTPException(status_code=503, detail=f"No se pudo clasificar: {error}")


@app.post("/preguntar")
def preguntar(datos: Pregunta):
    """Responde con streaming: una línea JSON por cada evento (fuentes, texto, fin)."""
    historial = [m.model_dump() for m in datos.historial]
    eventos = asistente.responder(datos.pregunta, historial)
    lineas = (json.dumps(evento, ensure_ascii=False) + "\n" for evento in eventos)
    return StreamingResponse(lineas, media_type="application/x-ndjson")


@app.get("/salud")
def salud():
    """Para comprobar que el servicio está vivo."""
    return {
        "estado": "ok",
        "modelo": clasificador.OLLAMA_MODELO,
        "trozos_asistente": len(asistente.indice),
    }
