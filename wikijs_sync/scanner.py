"""Escáner: recorre docs/ y convierte cada .md en datos de página."""
import re
import unicodedata
from pathlib import Path

from wikijs_sync.transform import split_front_matter, rewrite_links, add_notice, rewrite_images


def slugify(text):
    """Convierte un trozo de nombre en algo apto para una URL de wiki.

    Minúsculas, sin acentos, espacios -> guiones, solo [a-z0-9-].
    Ejemplo: 'Guía de Uso' -> 'guia-de-uso'
    """
    # Descompone los acentos (á -> a + tilde) y elimina la parte de la tilde
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    # Cualquier cosa que no sea letra/número pasa a guion
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Quita guiones sobrantes de los extremos
    return text.strip("-")


def split_locale(filename, default_locale):
    """Separa el locale (idioma) del nombre de un fichero según su sufijo.

    Convención: un sufijo de 2 letras antes de .md indica el idioma.
      'requisitos.va.md' -> locale 'va', nombre base 'requisitos.md'
      'requisitos.en.md' -> locale 'en', nombre base 'requisitos.md'
      'requisitos.md'    -> locale por defecto, nombre base 'requisitos.md'

    Devuelve (locale, nombre_base_con_md).
    """
    # p.ej. 'requisitos.va.md' -> partes ['requisitos', 'va', 'md']
    partes = filename.split(".")
    # Tiene sufijo de idioma si hay al menos 3 partes y la penúltima son 2 letras.
    if len(partes) >= 3 and len(partes[-2]) == 2 and partes[-2].isalpha():
        locale = partes[-2].lower()
        base = ".".join(partes[:-2]) + ".md"   # quita el sufijo de idioma
        return locale, base
    return default_locale, filename


def compute_path(rel_path, base_path):
    """Calcula el path de wiki a partir de la ruta relativa del fichero.

    - Quita la extensión .md
    - README.md / index.md -> la página de su carpeta
    - slugifica cada tramo de la ruta
    - antepone base_path

    Ejemplo: rel_path='instalacion/requisitos.md', base_path='pruebas'
             -> 'pruebas/instalacion/requisitos'

    NOTA: este path NO incluye el idioma. El sufijo de idioma (p.ej. '.va') debe
    haberse quitado ANTES de llamar aquí, para que 'requisitos.md' y
    'requisitos.va.md' compartan el mismo path (solo cambia el locale).
    """
    p = Path(rel_path)
    partes = list(p.parts)
    nombre = p.stem  # nombre sin extensión

    # Un índice de carpeta (README/index) representa a su carpeta,
    # así que se quita el último tramo y la página "es" la carpeta.
    if nombre.lower() in ("readme", "index"):
        partes = partes[:-1]
    else:
        partes[-1] = nombre  # sustituye 'requisitos.md' por 'requisitos'

    tramos = [slugify(x) for x in partes if x]
    base = [slugify(x) for x in Path(base_path).parts if x] if base_path else []
    return "/".join(base + tramos)


def extract_title(content, fallback):
    """Título = primer encabezado '# ...' del documento; si no, el fallback."""
    for linea in content.splitlines():
        m = re.match(r"^#\s+(.+)", linea.strip())
        if m:
            return m.group(1).strip()
    return fallback


def scan(docs_dir, base_path, default_locale="es", client=None):
    """Devuelve una lista de dicts, uno por cada .md encontrado.

    Separa el front matter y usa sus campos:
    - title: manda sobre el primer '#' del documento.
    - description: se toma del front matter (o cadena vacía).
    - tags: las del front matter (luego se les suma el tag de la herramienta).
    - locale: se detecta del sufijo del nombre (ej. 'guia.va.md' -> 'va');
      si no hay sufijo, se usa default_locale.

    Varios idiomas: 'guia.md' y 'guia.va.md' comparten el mismo path y se publican
    como la misma página en locales distintos (es y va).

    Además, detecta enlaces internos ROTOS (enlaces a .md que no existen en el
    repositorio) y los avisa por el log, sin detener la sincronización.
    """
    docs_dir = Path(docs_dir)
    ficheros = sorted(docs_dir.rglob("*.md"))

    # Lista de .md que existen, usando el nombre SIN el sufijo de idioma.
    # Así un enlace a 'guia.md' se considera válido aunque solo exista 'guia.va.md'
    # (y viceversa): las versiones de idioma cuentan como el mismo documento.
    known_files = set()
    for f in ficheros:
        rel = str(f.relative_to(docs_dir)).replace("\\", "/")
        carpeta = "/".join(rel.split("/")[:-1])
        _loc, nombre_base = split_locale(rel.split("/")[-1], default_locale)
        known_files.add(f"{carpeta}/{nombre_base}" if carpeta else nombre_base)

    broken = []  # se irá llenando con (fichero_origen, destino_roto)
    uploaded = {}  # imágenes ya subidas {ruta: nombre_en_wiki}, para no repetir
    n_imagenes = 0
    paginas = []
    for fichero in ficheros:
        rel = fichero.relative_to(docs_dir)
        rel_str = str(rel).replace("\\", "/")
        carpeta = "/".join(rel_str.split("/")[:-1])

        # Detectar el idioma por el sufijo del nombre y obtener el nombre limpio.
        locale, nombre_base = split_locale(rel_str.split("/")[-1], default_locale)
        rel_sin_idioma = f"{carpeta}/{nombre_base}" if carpeta else nombre_base

        bruto = fichero.read_text(encoding="utf-8")
        meta, contenido = split_front_matter(bruto)

        # El path se calcula con el nombre SIN el sufijo de idioma, para que las
        # versiones es/va compartan path (solo cambia el locale).
        path = compute_path(rel_sin_idioma, base_path)
        titulo = meta.get("title") or extract_title(contenido, fallback=Path(nombre_base).stem)
        descripcion = meta.get("description", "") or ""
        tags = meta.get("tags") or []
        if not isinstance(tags, list):
            tags = [tags]

        # Si hay cliente, subir las imágenes locales y reescribir sus rutas.
        # (Sin cliente -por ejemplo en los tests- no se tocan las imágenes.)
        if client is not None:
            antes = len(uploaded)
            contenido = rewrite_images(
                contenido, rel_str, docs_dir,
                upload=lambda ruta, nombre: (client.upload_asset(ruta, nombre), nombre)[1],
                uploaded=uploaded,
            )
            n_imagenes += len(uploaded) - antes

        # Orden importante: primero reescribir enlaces, después anteponer el aviso.
        contenido = rewrite_links(
            contenido, rel_sin_idioma, compute_path, base_path,
            known_files=known_files, broken=broken,
        )
        contenido = add_notice(contenido)

        paginas.append({
            "path": path,
            "title": titulo,
            "description": descripcion,
            "tags": [str(t) for t in tags],
            "content": contenido,
            "locale": locale,
            "source": rel_str,
        })

    # Avisar de las imágenes subidas (si las hubo).
    if n_imagenes:
        print(f"  {n_imagenes} imagen(es) subida(s) a la wiki.")

    # Avisar de los enlaces rotos encontrados (si los hay).
    if broken:
        print(f"\n  AVISO: {len(broken)} enlace(s) interno(s) roto(s):")
        for origen, destino in broken:
            print(f"    - en '{origen}' -> '{destino}' (el fichero no existe)")

    return paginas
