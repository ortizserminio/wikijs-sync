# Imagen base pequeña y estable, la que recomienda la guía y que se usará
# como imagen de job en GitLab CI.
FROM python:3.12-slim

WORKDIR /app

# Copiar e instalar dependencias ANTES del código aprovecha la caché de Docker:
# si solo cambia el código (no requirements.txt), no se reinstala todo.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el paquete de la herramienta.
COPY wikijs_sync ./wikijs_sync

# La herramienta se ejecuta como: python -m wikijs_sync <argumentos>
ENTRYPOINT ["python", "-m", "wikijs_sync"]
