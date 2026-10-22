# wikijs-sync

Herramienta de línea de comandos que sincroniza ficheros Markdown de un
repositorio con páginas de Wiki.js mediante su API GraphQL.

## Qué hace

Lee los `.md` de una carpeta (`docs/`), calcula la página que corresponde a
cada uno y crea, actualiza o borra páginas en Wiki.js para que la wiki refleje
el repositorio. La reconciliación es idempotente: ejecutarla dos veces seguidas
no cambia nada la segunda vez.

## Requisitos

- Python 3.12 o superior
- Dependencias: `pip install -r requirements.txt`

## Configuración

Crea un `wikijs-sync.yml` en la raíz del repositorio de conocimiento:

```yaml
base_path: pruebas/mi-proyecto   # rama de conocimiento en la wiki
docs_dir: docs                   # carpeta con los .md
locale: es                       # idioma de las páginas
tag: gitlab-sync                 # etiqueta que marca las páginas gestionadas
```

La URL y el token NO van en el fichero: llegan por variables de entorno.

## Variables de entorno

- `WIKI_URL`: URL base de la wiki (p.ej. `http://localhost:3000`)
- `WIKI_TOKEN`: API key de Wiki.js (grupo con permisos sobre `base_path`)

## Uso

```bash
python -m wikijs_sync --config wikijs-sync.yml
```

Opciones:
- `--dry-run`: muestra lo que haría sin tocar la wiki.
- `--prune`: borra las páginas gestionadas que ya no están en el repositorio.

## Pruebas

```bash
python -m pytest -v
```

## Docker

```bash
docker build -t wikijs-sync .
docker run --rm -e WIKI_URL -e WIKI_TOKEN -v ${PWD}:/app wikijs-sync --config wikijs-sync.yml
```
