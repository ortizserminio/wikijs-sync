"""Lanza la sincronización usando wikijs-sync.yml y las variables de entorno.

Provisional: en el incremento 4 esto se convierte en el CLI
(python -m wikijs_sync --config wikijs-sync.yml).
"""
from wikijs_sync.config import load_config
from wikijs_sync.wikijs import WikiJsClient
from wikijs_sync.sync import sync

cfg = load_config("wikijs-sync.yml")
client = WikiJsClient(cfg.wiki_url, cfg.wiki_token)

print(f"Sincronizando '{cfg.docs_dir}' -> wiki '{cfg.base_path}'\n")
sync(client, cfg)
