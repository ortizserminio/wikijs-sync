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

    return Config(
        base_path=datos["base_path"].strip("/"),
        docs_dir=datos["docs_dir"],
        locale=datos.get("locale", "es"),
        tag=datos.get("tag", "gitlab-sync"),
        wiki_url=wiki_url,
        wiki_token=wiki_token,
    )
