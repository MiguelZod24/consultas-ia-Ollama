"""
Evalúa el modelo con consultas cuya respuesta correcta ya conocemos.

Uso:  docker compose exec servicio-ia python evaluar.py
"""

import json
from pathlib import Path

import clasificador


def main():
    archivo = Path(__file__).with_name("consultas_prueba.json")
    consultas = json.loads(archivo.read_text(encoding="utf-8"))

    print(f"Evaluando {len(consultas)} consultas con {clasificador.OLLAMA_MODELO}...\n")

    aciertos = 0
    tiempos = []

    for numero, consulta in enumerate(consultas, start=1):
        try:
            resultado = clasificador.clasificar(consulta["texto"])
        except Exception as error:
            print(f"[{numero:>2}] ERROR  {consulta['texto']}\n       {error}")
            continue

        tiempos.append(resultado["tiempo_ms"])

        if resultado["categoria"] == consulta["esperada"]:
            aciertos += 1
            print(f"[{numero:>2}] OK     {consulta['texto']}")
        else:
            print(f"[{numero:>2}] FALLO  {consulta['texto']}")
            print(f"       esperada: {consulta['esperada']} | IA: {resultado['categoria']}")

    total = len(consultas)
    media = sum(tiempos) / len(tiempos) / 1000 if tiempos else 0

    print(f"\nResultado: {aciertos} de {total} aciertos ({aciertos / total:.0%})")
    print(f"Tiempo medio por consulta: {media:.1f} s")


if __name__ == "__main__":
    main()