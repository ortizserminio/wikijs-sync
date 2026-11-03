"""Escáner: recorre docs/ y convierte cada .md en datos de página."""
import posixpath
import re
import unicodedata
from pathlib import Path

from wikijs_sync.transform import (
    add_notice,
    rewrite_images,
    rewrite_links,
    split_front_matter,
)


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


def split_locale(filename, default_locale, allowed_locales=None):
    """Separa el locale (idioma) del nombre de un fichero según su sufijo.

    Convención: un sufijo de 2 letras antes de .md indica el idioma,
    PERO solo si está en la lista de idiomas permitidos.
      'requisitos.va.md' -> locale 'va', nombre base 'requisitos.md' (si 'va' está permitido)
      'setup.js.md'      -> locale por defecto, nombre base 'setup.js.md' ('js' no es idioma)

    Devuelve (locale, nombre_base_con_md).
    """
    partes = filename.split(".")
    if allowed_locales is None:
        allowed_locales = {default_locale}
    # Solo cuenta como idioma si es uno de los configurados.
    if len(partes) >= 3 and partes[-2].lower() in allowed_locales:
        locale = partes[-2].lower()
        base = ".".join(partes[:-2]) + ".md"
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
    # El base_path se respeta tal cual (sin slugify) para coincidir con los
    # permisos de la wiki, que distingue mayúsculas/minúsculas.
    base = list(Path(base_path).parts) if base_path else []
    return "/".join(base + tramos)

def asset_name(base_path, ruta_disco):
    """Nombre único y determinista de una imagen en la wiki.

    'pruebas/redes' + 'img/Diagrama Red.png' -> 'pruebas-redes--diagrama-red-1a2b3c4d.png'
    """
    import hashlib
    p = Path(ruta_disco)
    resumen = hashlib.sha1(p.read_bytes()).hexdigest()[:8]
    return f"{slugify(base_path)}--{slugify(p.stem)}-{resumen}{p.suffix.lower()}"


def extract_title(content, fallback):
    """Título = primer encabezado '# ...' del documento; si no, el fallback.

    IMPORTANTE: Ignora los encabezados dentro de bloques de código (``` o ~~~).
    Así un comentario de bash como '# instalar' no se toma como título.
    """
    # Eliminar bloques de código antes de buscar el título
    # Patrón: ```...``` o ~~~...~~~ (multilínea)
    contenido_sin_codigo = re.sub(r"```[\s\S]*?```|~~~[\s\S]*?~~~", "", content)
    # También eliminar código inline `...`
    contenido_sin_codigo = re.sub(r"`[^`\n]+`", "", contenido_sin_codigo)

    for linea in contenido_sin_codigo.splitlines():
        m = re.match(r"^#\s+(.+)", linea.strip())
        if m:
            return m.group(1).strip()
    return fallback



class ScanError(Exception):
    """Error durante el escaneo de documentos."""


def scan(
    docs_dir, base_path, default_locale="es", client=None, allowed_locales=None, source_url=None
):

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

    Lanza ScanError si docs_dir no existe o no contiene ningún .md (protección
    contra borrados accidentales con --prune).
    """
    docs_dir = Path(docs_dir)

    # Protección crítica: abortar si docs_dir no existe o está vacío.
    # Sin esto, --prune borraría TODAS las páginas gestionadas.
    if not docs_dir.exists():
        raise ScanError(
            f"La carpeta docs_dir '{docs_dir}' no existe. "
            f"Revisa el valor de docs_dir en wikijs-sync.yml."
        )

    ficheros = sorted(docs_dir.rglob("*.md"))

    if not ficheros:
        raise ScanError(
            f"La carpeta '{docs_dir}' no contiene ningún fichero .md. "
            f"¿Está bien configurado docs_dir en wikijs-sync.yml?"
        )

    # Lista de .md que existen, usando el nombre SIN el sufijo de idioma.
    # Así un enlace a 'guia.md' se considera válido aunque solo exista 'guia.va.md'
    # (y viceversa): las versiones de idioma cuentan como el mismo documento.
    known_files = set()
    for f in ficheros:
        rel = str(f.relative_to(docs_dir)).replace("\\", "/")
        carpeta = "/".join(rel.split("/")[:-1])
        _loc, nombre_base = split_locale(rel.split("/")[-1], default_locale, allowed_locales)
        known_files.add(f"{carpeta}/{nombre_base}" if carpeta else nombre_base)

    # Assets que ya están en la wiki (para no volver a subirlos).
    existentes = client.list_asset_names() if client is not None else set()

    def subir(ruta_disco, _nombre):
        """Calcula el nombre en la wiki y sube la imagen solo si hace falta."""
        nombre_wiki = asset_name(base_path, ruta_disco)
        if client is not None and nombre_wiki not in existentes:
            client.upload_asset(ruta_disco, nombre_wiki)
            existentes.add(nombre_wiki)
        return nombre_wiki

    broken = []  # se irá llenando con (fichero_origen, destino_roto)
    uploaded = {}  # imágenes ya subidas {ruta: nombre_en_wiki}, para no repetir
    n_imagenes = 0
    paginas = []
    for fichero in ficheros:
        rel = fichero.relative_to(docs_dir)
        rel_str = str(rel).replace("\\", "/")
        carpeta = "/".join(rel_str.split("/")[:-1])

        # Detectar el idioma por el sufijo del nombre y obtener el nombre limpio.
        locale, nombre_base = split_locale(rel_str.split("/")[-1], default_locale, allowed_locales)
        rel_sin_idioma = f"{carpeta}/{nombre_base}" if carpeta else nombre_base

        # utf-8-sig ignora el BOM de Windows (evita romper el front matter).
        bruto = fichero.read_text(encoding="utf-8-sig")
        meta, contenido = split_front_matter(bruto)

        # El path se calcula con el nombre SIN el sufijo de idioma, para que las
        # versiones es/va compartan path (solo cambia el locale).
        path = compute_path(rel_sin_idioma, base_path)
        titulo = meta.get("title") or extract_title(contenido, fallback=Path(nombre_base).stem)
        descripcion = meta.get("description", "") or ""
        tags = meta.get("tags") or []
        if not isinstance(tags, list):
            tags = [tags]


        # Subir las imágenes locales y reescribir sus rutas.
        # Se hace siempre (incluso sin cliente) para que dry-run calcule el mismo contenido.
        antes = len(uploaded)
        contenido = rewrite_images(
            contenido, rel_str, docs_dir,
            upload=subir,
            uploaded=uploaded,
        )
        n_imagenes += len(uploaded) - antes


        # Orden importante: primero reescribir enlaces, después anteponer el aviso.
        contenido = rewrite_links(
            contenido, rel_sin_idioma, compute_path, base_path,
            known_files=known_files, broken=broken,
            allowed_locales=allowed_locales,
        )

        enlace = None
        if source_url:
            ruta_repo = posixpath.join(str(docs_dir).replace("\\", "/"), rel_str)
            enlace = f"{source_url.rstrip('/')}/{ruta_repo}"
        contenido = add_notice(contenido, enlace)



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

    # Detectar colisiones de path (varios ficheros generan el mismo path+locale).
    # Esto puede pasar con Guía.md vs guia.md, o README.md vs index.md.
    vistos = {}  # {(path, locale): fichero_origen}
    colisiones = []
    for p in paginas:
        clave = (p["path"], p["locale"])
        if clave in vistos:
            colisiones.append((p["source"], vistos[clave], p["path"], p["locale"]))
        else:
            vistos[clave] = p["source"]

    if colisiones:
        msg = "Colisión de paths: varios ficheros generan la misma página.\n"
        for nuevo, existente, path, locale in colisiones:
            msg += f"  - '{nuevo}' y '{existente}' → {path} [{locale}]\n"
        msg += "Renombra uno de los ficheros para evitar que se pisen."
        raise ScanError(msg)

    return paginas, broken
