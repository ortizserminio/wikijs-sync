# wikijs-sync

Herramienta de línea de comandos que sincroniza ficheros Markdown de un
repositorio con páginas de Wiki.js mediante su API GraphQL.

La idea: el **repositorio es la fuente de verdad** y la wiki es la forma cómoda
de leer su contenido. Cada vez que se hace push de los `.md`, un pipeline ejecuta
esta herramienta y la wiki queda actualizada automáticamente.

> ¿Eres un equipo que quiere conectar su repositorio con la wiki? Sigue la
> **[Guía de uso](GUIA-DE_USO.md)**: te lleva paso a paso sin necesidad de conocer
> la herramienta por dentro.

## Qué hace

Lee los `.md` de una carpeta (`docs/`), calcula la página que corresponde a cada
uno y crea, actualiza o borra páginas en Wiki.js para que la wiki refleje el
repositorio. La reconciliación es **idempotente**: ejecutarla dos veces seguidas
no cambia nada la segunda vez.

### Características
- **Crear / actualizar / borrar** páginas (reconciliación completa).
- **Idempotente**: solo toca lo que cambió.
- **Respeta las páginas hechas a mano**: solo gestiona las que llevan su tag y
  cuelgan de su `base_path`; nunca toca otras (ni con `--prune`).
- **Front matter**: usa `title`, `description` y `tags` si existen.
- **Enlaces relativos**: reescribe los enlaces a otros `.md` como rutas de la wiki.
- **Enlaces rotos**: avisa en el log de los enlaces internos que apuntan a
  ficheros que no existen.
- **Varios idiomas**: un sufijo en el nombre (ej. `guia.ca.md`) publica la misma
  página en otro idioma (mismo path, distinto locale).
- **Imágenes**: sube las imágenes locales a los assets de Wiki.js y reescribe sus
  rutas en el Markdown.
- **Diagramas mermaid**: se ven tal cual (Wiki.js los dibuja al mostrarlos).
- **Aviso en cada página**: nota de "página autogenerada, no editar en la wiki".
- Modos `--dry-run` (ver sin tocar) y `--prune` (borrar lo que ya no está).

## Requisitos
- Python 3.12 o superior.
- Dependencias: `requests` y `PyYAML` (se instalan con el paquete).

## Instalación
```bash
pip install .
# o en modo editable para desarrollo:
pip install -e .
```

## Configuración

Cada repositorio de conocimiento lleva en su raíz un `wikijs-sync.yml`:

```yaml
base_path: conocimiento/sistemas/redes   # rama de conocimiento en la wiki
docs_dir: docs                           # carpeta con los .md
locale: es                               # idioma por defecto de las páginas
tag: gitlab-sync                         # etiqueta que marca las páginas gestionadas
```

La URL de la wiki y el token NO van en el fichero: llegan por variables de entorno.

### Variables de entorno
- `WIKI_URL`: URL base de la wiki (p.ej. `http://localhost:3000`).
- `WIKI_TOKEN`: API key de Wiki.js (de un grupo con permisos sobre `base_path`
  y sobre los assets si se usan imágenes).

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
La herramienta se empaqueta en una imagen que lleva todo preinstalado:
```bash
docker build -t wikijs-sync .
docker run --rm -e WIKI_URL -e WIKI_TOKEN -v ${PWD}:/app wikijs-sync --config wikijs-sync.yml
```

## Integración continua (CI)

Cada repositorio de conocimiento define un pipeline que, al hacer push a la rama
por defecto, ejecuta la herramienta y sincroniza su zona de la wiki.

Hay **dos variantes** según cómo se provee la herramienta al job:
- **Imagen preconstruida (A)** (recomendada si hay Container Registry): el job usa
  una imagen que ya lleva la herramienta. Rápido, no instala nada en cada ejecución.
- **Instalación al vuelo (B)**: el job usa una imagen oficial de Python e instala la
  herramienta con `pip` en cada ejecución. No necesita registry, pero es más lento.

Y funciona con distintos sistemas de CI (el concepto es el mismo, cambia el fichero):
- **GitLab CI**: plantilla reutilizable en `templates/wikijs-sync.gitlab-ci.yml`, que
  los repos incorporan con `include` (ver la Guía de uso).
- **Jenkins** (lo usa la UMH): el pipeline se define en un `Jenkinsfile` (Groovy). Hay
  ejemplos de las dos variantes (A y B) como referencia.
- **GitHub Actions**: usado para los ensayos (workflows en `.github/workflows/`).

## Estructura del proyecto
```
wikijs-sync/
  wikijs_sync/
    __main__.py      # punto de entrada: python -m wikijs_sync
    cli.py           # argumentos: --config, --dry-run, --prune
    config.py        # lee wikijs-sync.yml y las variables de entorno
    scanner.py       # recorre docs/ y calcula path, título, locale y contenido
    transform.py     # front matter, enlaces, enlaces rotos, imágenes, aviso
    wikijs.py        # cliente: listar, crear, actualizar, borrar, subir assets
    sync.py          # reconciliación: decide qué crear, actualizar o borrar
  tests/             # pruebas unitarias (pytest)
  templates/         # plantilla de CI compartida (GitLab)
  .github/workflows/ # workflows de GitHub Actions (CI y build de la imagen)
  Dockerfile         # receta de la imagen propia (variante A)
  pyproject.toml     # empaquetado (hace la herramienta instalable con pip)
  GUIA-DE_USO.md     # guía paso a paso para equipos
  README.md
```
