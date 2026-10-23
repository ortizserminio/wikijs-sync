"""Reconciliación: compara los .md con la wiki y crea/actualiza/borra páginas."""
from wikijs_sync.scanner import scan


def _wiki_pages_by_path(client, cfg):
    """Devuelve {path: pagina} de las páginas gestionadas por la herramienta.

    Solo las que cuelgan del base_path y llevan nuestro tag, para no tocar
    nunca páginas creadas a mano.
    """
    gestionadas = {}
    for p in client.list_pages():
        if not p["path"].startswith(cfg.base_path):
            continue
        tags = p.get("tags") or []
        if cfg.tag not in tags:
            continue
        # Clave (path, locale): una misma ruta puede existir en varios idiomas.
        gestionadas[(p["path"], p["locale"])] = p
    return gestionadas


def sync(client, cfg, dry_run=False, prune=False):
    """Ejecuta la reconciliación y devuelve un resumen de lo hecho.

    - dry_run: no toca la wiki, solo muestra lo que haría.
    - prune: borra las páginas gestionadas que ya no están en el repo.
    """
    # En dry-run no subimos imágenes (no se toca la wiki); si no, pasamos el cliente.
    deseadas = scan(
        cfg.docs_dir, cfg.base_path, default_locale=cfg.locale,
        client=None if dry_run else client,
    )
    en_wiki = _wiki_pages_by_path(client, cfg)
    # Claves deseadas como (path, locale), porque una ruta puede existir en varios idiomas.
    claves_deseadas = {(p["path"], p["locale"]) for p in deseadas}

    creadas = actualizadas = sin_cambios = borradas = 0
    marca = "[dry-run] " if dry_run else ""

    # --- Crear y actualizar ---
    for pagina in deseadas:
        path = pagina["path"]
        locale = pagina["locale"]           # locale propio de esta página (es, va, ...)
        titulo = pagina["title"]
        contenido = pagina["content"]
        descripcion = pagina.get("description", "")
        # Combina las tags del fichero con el tag de la herramienta (sin duplicar).
        tags = list(dict.fromkeys(pagina.get("tags", []) + [cfg.tag]))
        clave = (path, locale)
        etiqueta = f"{path} [{locale}]"      # para el log, mostrando el idioma

        if clave not in en_wiki:
            if not dry_run:
                client.create_page(
                    path=path, title=titulo, content=contenido,
                    description=descripcion, tags=tags, locale=locale,
                )
            creadas += 1
            print(f"  {marca}+ crear      {etiqueta}")
        else:
            actual = client.get_page(en_wiki[clave]["id"])
            if actual["content"] == contenido and actual["title"] == titulo:
                sin_cambios += 1
                print(f"  = sin cambio {etiqueta}")
            else:
                if not dry_run:
                    client.update_page(
                        page_id=en_wiki[clave]["id"],
                        path=path, title=titulo, content=contenido,
                        description=descripcion, tags=tags, locale=locale,
                    )
                actualizadas += 1
                print(f"  {marca}~ actualizar {etiqueta}")

    # --- Borrar (solo con --prune) ---
    if prune:
        for clave, pagina in en_wiki.items():
            if clave not in claves_deseadas:
                if not dry_run:
                    client.delete_page(pagina["id"])
                borradas += 1
                path, locale = clave
                print(f"  {marca}- borrar     {path} [{locale}]")

    print(
        f"\nResumen: {creadas} creadas, {actualizadas} actualizadas, "
        f"{borradas} borradas, {sin_cambios} sin cambios."
        + ("  (dry-run: no se ha tocado la wiki)" if dry_run else "")
    )
    return {
        "creadas": creadas, "actualizadas": actualizadas,
        "borradas": borradas, "sin_cambios": sin_cambios,
    }
