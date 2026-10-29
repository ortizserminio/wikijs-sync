"""Punto de entrada por línea de comandos de la herramienta."""
import argparse
import sys

from wikijs_sync.config import load_config
from wikijs_sync.wikijs import WikiJsClient
from wikijs_sync.sync import sync


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="wikijs_sync",
        description="Sincroniza ficheros Markdown de un repositorio con Wiki.js.",
    )
    parser.add_argument(
        "--config", default="wikijs-sync.yml",
        help="ruta del fichero de configuración (por defecto: wikijs-sync.yml)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="muestra lo que haría sin tocar la wiki",
    )
    parser.add_argument(
        "--prune", action="store_true",
        help="borra las páginas gestionadas que ya no están en el repositorio",
    )
    args = parser.parse_args(argv)

    try:
        cfg = load_config(args.config)
    except Exception as e:
        print(f"Error de configuración: {e}", file=sys.stderr)
        return 2

    client = WikiJsClient(cfg.wiki_url, cfg.wiki_token)
    print(f"Sincronizando '{cfg.docs_dir}' -> wiki '{cfg.base_path}'\n")

    try:
        resumen = sync(client, cfg, dry_run=args.dry_run, prune=args.prune)
    except Exception as e:
        # Fallo general: wiki caída, token incorrecto al listar...
        print(f"Error durante la sincronización: {e}", file=sys.stderr)
        return 1

    if resumen["errores"]:
        print(f"{len(resumen['errores'])} página(s) con error.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
