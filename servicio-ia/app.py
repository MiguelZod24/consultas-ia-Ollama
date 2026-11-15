from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import clasificador

app = FastAPI(title="Servicio de IA - Clasificador de consultas")


# Cómo tiene que ser lo que nos envía PHP
class Consulta(BaseModel):
    texto: str = Field(min_length=1, max_length=2000)


@app.post("/clasificar")
def clasificar(consulta: Consulta):
    """PHP llama aquí con {"texto": "..."} y recibe la clasificación."""
    try:
        return clasificador.clasificar(consulta.texto)
    except Exception as error:
        # Si la IA falla, avisamos a PHP con un error claro
        raise HTTPException(status_code=503, detail=f"No se pudo clasificar: {error}")


@app.get("/salud")
def salud():
    """Para comprobar que el servicio está vivo."""
    return {"estado": "ok", "modelo": clasificador.OLLAMA_MODELO}
