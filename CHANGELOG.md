# Changelog

Todos los cambios notables de este proyecto se documentan en este fichero.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y el proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [0.2.0] - 2026-10-26

### Añadido
- Protección contra `--prune` destructivo: aborta si `docs_dir` no existe o está vacío.
- Tag único por repositorio (`gitlab-sync:<base_path>`) para evitar conflictos entre repos con paths anidados.
- Soporte para `locale_map` en la configuración: permite usar `.va.md` en ficheros que se publican como `ca`.
- Detección de colisiones de path (`Guía.md` vs `guia.md`, `README.md` vs `index.md`).
- Los enlaces a versiones en otro idioma (`guia.va.md`) generan el path correcto.
- Lint con `ruff` en el CI de GitHub.
- Este fichero CHANGELOG.

### Corregido
- Los enlaces e imágenes dentro de bloques de código ya no se reescriben.
- El título de la página ya no puede salir de un comentario dentro de un bloque de código.
- Los ficheros con BOM de Windows ya no rompen el front matter (`utf-8-sig`).
- Avisos de estilo corregidos (imports, espacios, líneas largas).

### Cambiado
- Versión actualizada a 0.2.0.
- La imagen Docker ahora se publica también con tag de versión (`0.2.0`), no solo `latest`.
- El Jenkinsfile ahora recomienda usar HTTPS y fijar la versión de la herramienta.
- La plantilla de GitLab CI ahora usa `v0.2.0` por defecto en vez de `main`.

## [0.1.0] - 2026-10-20

### Añadido
- Sincronización básica de ficheros `.md` con Wiki.js.
- Soporte para front matter (title, description, tags).
- Reescritura de enlaces relativos a rutas de wiki.
- Subida de imágenes locales a assets de Wiki.js.
- Detección de enlaces rotos (aviso, no error).
- Aviso de "página autogenerada" con enlace al fichero origen.
- Soporte multi-idioma con sufijos (`.va.md`, `.ca.md`).
- Modos `--dry-run` y `--prune`.
- Dockerfile para empaquetado.
- CI con GitHub Actions (tests + publicación de imagen).
- Plantillas para GitLab CI y Jenkins.
- Documentación: README, GUIA-DE-USO.
