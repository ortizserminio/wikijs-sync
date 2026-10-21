"""Escáner: recorre docs/ y convierte cada .md en datos de página."""
import re
import unicodedata
from pathlib import Path

from wikijs_sync.transform import split_front_matter, rewrite_links, add_notice


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


def compute_path(rel_path, base_path):
    """Calcula el path de wiki a partir de la ruta relativa del fichero.

    - Quita la extensión .md
    - README.md / index.md -> la página de su carpeta
    - slugifica cada tramo de la ruta
    - antepone base_path

    Ejemplo: rel_path='instalacion/requisitos.md', base_path='pruebas'
             -> 'pruebas/instalacion/requisitos'
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


def scan(docs_dir, base_path):
    """Devuelve una lista de dicts, uno por cada .md encontrado.

    Separa el front matter y usa sus campos:
    - title: manda sobre el primer '#' del documento.
    - description: se toma del front matter (o cadena vacía).
    - tags: las del front matter (luego se les suma el tag de la herramienta).
    """
    docs_dir = Path(docs_dir)
    paginas = []
    for fichero in sorted(docs_dir.rglob("*.md")):
        rel = fichero.relative_to(docs_dir)
        bruto = fichero.read_text(encoding="utf-8")
        meta, contenido = split_front_matter(bruto)

        path = compute_path(rel, base_path)
        # El title del front matter manda; si no, el primer '#'; si no, el nombre.
        titulo = meta.get("title") or extract_title(contenido, fallback=fichero.stem)
        descripcion = meta.get("description", "") or ""
        tags = meta.get("tags") or []
        if not isinstance(tags, list):
            tags = [tags]

        # Orden importante: primero reescribir enlaces sobre el contenido real,
        # y DESPUÉS anteponer el aviso.
        source_rel = str(rel).replace("\\", "/")
        contenido = rewrite_links(contenido, source_rel, compute_path, base_path)
        contenido = add_notice(contenido)

        paginas.append({
            "path": path,
            "title": titulo,
            "description": descripcion,
            "tags": [str(t) for t in tags],
            "content": contenido,
            "source": str(rel).replace("\\", "/"),
        })
    return paginas
