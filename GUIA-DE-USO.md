# Guía de uso: conecta tu repositorio con la wiki

Esta guía explica, paso a paso, cómo conectar el repositorio de tu equipo con
Wiki.js para que tu documentación se publique sola. No necesitas saber cómo
funciona la herramienta por dentro: solo seguir estos pasos.

Cuando termines, cada vez que hagas push de tus `.md`, tu documentación aparecerá
(o se actualizará) automáticamente en la wiki, en la zona de tu equipo.

---

## Antes de empezar: qué necesitas

- Un repositorio en el GitLab de la universidad con tu documentación.
- Tus ficheros Markdown (`.md`) dentro de una carpeta `docs/`.
- Que el equipo de la wiki te haya dado:
  - La **ruta de tu equipo** en la wiki (tu `base_path`, p.ej. `conocimiento/sistemas/redes`).
  - Acceso para que el pipeline pueda escribir en esa ruta (lo configura quien
    administra la wiki; tú no tienes que hacer nada con el token).

Si no tienes la ruta o el acceso, pídelos antes de seguir.

---

## Paso 1: organiza tu documentación en `docs/`

Pon tus ficheros Markdown dentro de una carpeta `docs/` en la raíz del repositorio:

```
mi-repo/
  docs/
    index.md
    instalacion.md
    ...
```

Reglas útiles que conviene conocer:
- `index.md` (o `README.md`) dentro de una carpeta se convierte en la página de esa carpeta.
- El nombre del fichero define la dirección de la página en la wiki (sin extensión,
  en minúsculas, sin acentos ni espacios: `Guía de Uso.md` -> `guia-de-uso`).
- Puedes poner un bloque de metadatos al principio de cada `.md` (opcional):
  ```
  ---
  title: Título de la página
  description: Una frase que describe la página
  tags: [etiqueta1, etiqueta2]
  ---
  ```
- Para publicar una página en otro idioma, añade un sufijo al nombre: `index.ca.md`
  (catalán), `index.en.md` (inglés). Sin sufijo = idioma por defecto.

---

## Paso 2: crea el fichero `wikijs-sync.yml`

En la raíz del repositorio, crea un fichero `wikijs-sync.yml` con la configuración
de tu equipo:

```yaml
base_path: conocimiento/sistemas/redes   # LA RUTA DE TU EQUIPO (te la dan)
docs_dir: docs                           # la carpeta con tus .md
locale: es                               # idioma por defecto
tag: gitlab-sync                         # no lo cambies (marca las páginas gestionadas)
```

Solo tienes que ajustar `base_path` con la ruta que te hayan asignado. El resto
suele dejarse igual.

---

## Paso 3: añade el pipeline (`.gitlab-ci.yml`)

En la raíz del repositorio, crea un fichero `.gitlab-ci.yml` que incorpora la
plantilla compartida de la herramienta:

```yaml
include:
  - project: 'GRUPO/wikijs-sync'                 # repo de la herramienta
    ref: v1                                       # versión de la plantilla
    file: '/templates/wikijs-sync.gitlab-ci.yml'  # la plantilla
```

Con estas tres líneas, tu repositorio hereda todo el proceso de sincronización.
No tienes que copiar ni entender la lógica; solo incluirla.

(Pregunta a quien administra la herramienta cuál es la ruta exacta del `project`
y el `ref` a usar.)

---

## Paso 4: haz push y comprueba

```bash
git add .
git commit -m "Conecta la documentación con la wiki"
git push
```

Al hacer push a la rama principal:
1. El pipeline se ejecuta solo (lo ves en tu proyecto, en Build -> Pipelines).
2. Lee tus `.md` y los publica en la wiki, bajo tu `base_path`.
3. Cuando el pipeline esté en verde, abre la wiki y comprueba tus páginas.

---

## Qué ocurre a partir de ahora

- Cada push a la rama principal **actualiza** tu zona de la wiki.
- Si **editas** un `.md`, su página se actualiza.
- Si **borras** un `.md`, su página se elimina de la wiki.
- **No edites las páginas directamente en la wiki**: se generan desde el repositorio
  y los cambios hechos a mano se perderían en la siguiente sincronización. Cada página
  lleva un aviso recordándolo.

---

## Problemas frecuentes

- **El pipeline falla con error de permisos**: la ruta (`base_path`) o el acceso no
  están bien configurados. Contacta con quien administra la wiki.
- **No veo mi página en la wiki**: comprueba la URL con el prefijo de idioma
  (`/es/...`) y que el pipeline terminó en verde.
- **El pipeline no se ejecuta**: revisa que el `.gitlab-ci.yml` y el `wikijs-sync.yml`
  están en la raíz del repositorio y bien escritos.

---

## Resumen (lo mínimo que tienes que hacer)

1. `docs/` con tus `.md`.
2. `wikijs-sync.yml` con tu `base_path`.
3. `.gitlab-ci.yml` con el `include` de la plantilla.
4. `git push` y comprobar el pipeline y la wiki.
