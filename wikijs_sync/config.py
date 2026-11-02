"""Carga la configuración: wikijs-sync.yml + variables de entorno."""
import os
from dataclasses import dataclass

import yaml


@dataclass
class Config:
    """Agrupa todos los datos de configuración en un solo objeto."""
    base_path: str
    docs_dir: str
    locale: str
    tag: str
    locales: list
    locale_map: dict  # mapeo de idiomas: {'va': 'ca'} -> los .va.md se publican como ca
    source_url: str 
    wiki_url: str
    wiki_token: str


def load_config(config_path="wikijs-sync.yml"):
    """Lee el YAML de configuración y los secretos de las variables de entorno.

    La URL y el token NO van en el YAML: llegan por WIKI_URL y WIKI_TOKEN,
    para no guardar secretos en ficheros que podrían acabar en Git.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        datos = yaml.safe_load(f)

    wiki_url = os.environ.get("WIKI_URL")
    wiki_token = os.environ.get("WIKI_TOKEN")
    if not wiki_url or not wiki_token:
        raise RuntimeError(
            "Faltan las variables de entorno WIKI_URL y/o WIKI_TOKEN."
        )

    locale = datos.get("locale", "es")
    # Idiomas admitidos como sufijo. Siempre incluye el principal.
    locales = {str(l).lower() for l in datos.get("locales", [])} | {locale}
    
    # Mapeo de idiomas: permite usar .va.md en los ficheros pero publicar como 'ca'.
    locale_map = {str(k).lower(): str(v).lower() for k, v in datos.get("locale_map", {}).items()}
    
    # Avisar de claves desconocidas en el YAML (ayuda a detectar typos).
    claves_conocidas = {"base_path", "docs_dir", "locale", "locales", "locale_map", "tag", "source_url"}
    desconocidas = set(datos.keys()) - claves_conocidas
    if desconocidas:
        print(f"  AVISO: claves desconocidas en wikijs-sync.yml: {', '.join(sorted(desconocidas))}")

    # Tag único por repo: incluye el base_path para evitar conflictos entre repos
    # con base_paths anidados (ej: conocimiento/sistemas vs conocimiento/sistemas/redes).
    tag_base = datos.get("tag", "gitlab-sync")
    base_path = datos["base_path"].strip("/")
    tag = f"{tag_base}:{base_path}"

    return Config(
        base_path=base_path,
        docs_dir=datos["docs_dir"],
        locale=locale,
        tag=tag,
        locales=sorted(locales),
        locale_map=locale_map,
        source_url=datos.get("source_url", ""),
        wiki_url=wiki_url,
        wiki_token=wiki_token,
    )
     
