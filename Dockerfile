# Imagen base pequeña y estable, la que recomienda la guía y que se usará
# como imagen de job en GitLab CI.
FROM python:3.12-slim

# Logs sin buffer (se ven al instante en el pipeline) y pip sin caché ni avisos.
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

# Copiar los ficheros de empaquetado y el código, e INSTALAR la herramienta.
# Instalarla (no solo copiarla) la deja accesible desde cualquier carpeta,
# que es lo que necesita el job al ejecutarse desde la raíz del repo de conocimiento.
# Se instala desde pyproject.toml -> solo dependencias de producción (requests, PyYAML),
# SIN pytest, así la imagen es más ligera.
COPY pyproject.toml ./
COPY wikijs_sync ./wikijs_sync
RUN pip install .

# La herramienta se ejecuta como: python -m wikijs_sync <argumentos>
ENTRYPOINT ["python", "-m", "wikijs_sync"]
