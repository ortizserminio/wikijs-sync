"""Transformaciones del contenido Markdown antes de enviarlo a Wiki.js."""
import posixpath
import re

import yaml


def split_front_matter(text):
    """Separa el front matter (bloque entre '---') del contenido.

    Devuelve una tupla (metadatos: dict, contenido: str).
    Si no hay front matter, devuelve ({}, texto original).

    Ejemplo de entrada:
        ---
        title: Hola
        tags: [a, b]
        ---
        # Cuerpo
    -> ({"title": "Hola", "tags": ["a", "b"]}, "# Cuerpo")
    """
    # El front matter solo cuenta si el fichero EMPIEZA por '---'
    if not text.startswith("---"):
        return {}, text

    lineas = text.splitlines()
    # lineas[0] es el '---' de apertura; buscamos el '---' de cierre
    cierre = None
    for i in range(1, len(lineas)):
        if lineas[i].strip() == "---":
            cierre = i
            break

    if cierre is None:
        # '---' de apertura sin cierre: no es front matter válido
        return {}, text

    bloque = "\n".join(lineas[1:cierre])
    contenido = "\n".join(lineas[cierre + 1:]).lstrip("\n")

    try:
        datos = yaml.safe_load(bloque) or {}
    except yaml.YAMLError:
        datos = {}

    if not isinstance(datos, dict):
        datos = {}

    return datos, contenido


# Enlaces markdown: [texto](destino). Captura el texto y el destino por separado.
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def rewrite_links(content, source_rel, compute_path, base_path, known_files=None, broken=None):
    """Reescribe los enlaces relativos a .md como rutas de la wiki.

    - content:      el texto markdown de la página.
    - source_rel:   ruta del fichero actual relativa a docs_dir (p.ej.
                    'instalacion/requisitos.md'), para resolver los enlaces.
    - compute_path: la función del escáner que calcula el path de wiki.
    - base_path:    el prefijo de la rama de conocimiento.
    - known_files:  conjunto (set) con las rutas relativas de TODOS los .md del repo.
                    Si se pasa, se detectan enlaces rotos (destinos que no existen).
    - broken:       lista donde se añaden los enlaces rotos encontrados, como tuplas
                    (fichero_origen, destino). Si se pasa, se rellena por efecto lateral.

    Solo toca enlaces relativos que apuntan a ficheros .md. Deja intactos los
    enlaces externos (http...), anclas (#...) y los que no son .md.
    """
    carpeta = posixpath.dirname(source_rel.replace("\\", "/"))

    def _sub(match):
        texto, destino = match.group(1), match.group(2)

        # No tocar externos, anclas, ni enlaces que no sean a .md
        if destino.startswith(("http://", "https://", "#", "mailto:", "/")):
            return match.group(0)
        # Separar un posible ancla (#seccion) del final
        ancla = ""
        if "#" in destino:
            destino, ancla = destino.split("#", 1)
            ancla = "#" + ancla
        if not destino.endswith(".md"):
            return match.group(0)

        # Resolver el destino respecto a la carpeta del fichero actual
        objetivo = posixpath.normpath(posixpath.join(carpeta, destino))

        # Detección de enlaces rotos: si tenemos la lista de ficheros del repo y
        # el destino no está en ella, es un enlace a un fichero que no existe.
        if known_files is not None and objetivo not in known_files:
            if broken is not None:
                broken.append((source_rel.replace("\\", "/"), destino))

        wiki_path = compute_path(objetivo, base_path)
        return f"[{texto}](/{wiki_path}{ancla})"

    return _LINK_RE.sub(_sub, content)


def add_notice(content, notice=None):
    """Antepone al contenido un aviso de página autogenerada."""
    if notice is None:
        notice = (
            "> Esta página se genera automáticamente desde el repositorio. "
            "No la edites aquí: los cambios se perderán en la próxima sincronización."
        )
    return f"{notice}\n\n{content}"


# Imágenes markdown: ![texto](destino). El '!' al principio las distingue de los enlaces.
_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

# Extensiones de imagen que vamos a gestionar.
_IMG_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")


def rewrite_images(content, source_rel, docs_dir, upload, uploaded=None):
    """Sube las imágenes locales y reescribe sus rutas a la ruta de la wiki.

    - content:    el texto markdown.
    - source_rel: ruta del .md actual relativa a docs_dir (para resolver rutas relativas).
    - docs_dir:   carpeta raíz de los .md (para localizar el fichero de imagen en disco).
    - upload:     función upload(ruta_fichero, nombre) que sube la imagen y la deja
                  accesible en /<nombre> en la wiki. Devuelve el nombre usado.
    - uploaded:   dict opcional {ruta_local: nombre_en_wiki} para no subir dos veces la misma.

    Solo toca imágenes locales (no http). Deja intactas las externas.
    """
    import os

    carpeta = posixpath.dirname(source_rel.replace("\\", "/"))
    if uploaded is None:
        uploaded = {}

    def _sub(match):
        texto, destino = match.group(1), match.group(2)

        # No tocar imágenes externas ni rutas absolutas
        if destino.startswith(("http://", "https://", "/")):
            return match.group(0)
        if not destino.lower().endswith(_IMG_EXTS):
            return match.group(0)

        # Resolver la ruta de la imagen respecto al .md actual
        objetivo = posixpath.normpath(posixpath.join(carpeta, destino))
        ruta_disco = os.path.join(str(docs_dir), *objetivo.split("/"))

        if not os.path.isfile(ruta_disco):
            # La imagen no existe en el repo: no se puede subir, se deja el enlace tal cual.
            return match.group(0)

        # Subir solo una vez cada imagen (puede estar referenciada en varios sitios)
        if objetivo in uploaded:
            nombre_wiki = uploaded[objetivo]
        else:
            nombre_wiki = upload(ruta_disco, os.path.basename(objetivo))
            uploaded[objetivo] = nombre_wiki

        # En la wiki, un asset de la raíz queda accesible en /<nombre>
        return f"![{texto}](/{nombre_wiki})"

    return _IMG_RE.sub(_sub, content)
