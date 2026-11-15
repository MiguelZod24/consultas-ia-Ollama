# Partimos de una imagen oficial con Python ya instalado
FROM python:3.12-slim

WORKDIR /app

# Instalamos las librerías
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Arrancamos la ventanilla en el puerto 8000
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
