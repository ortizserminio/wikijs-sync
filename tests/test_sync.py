"""Pruebas de la reconciliación con un cliente falso (sin wiki real)."""
from wikijs_sync.config import Config
from wikijs_sync.sync import sync

class ClienteFalso:
    """Imita a WikiJsClient guardando en memoria lo que se le pide."""

    def __init__(self, paginas, falla_en=None):
        self.paginas = paginas
        self.falla_en = falla_en      # path en el que create_page lanza error
        self.creadas, self.actualizadas, self.borradas = [], [], []

    def list_pages(self):
        return self.paginas

    def list_asset_names(self):
        return set()

    def get_page(self, page_id):
        return next(p for p in self.paginas if p["id"] == page_id)

    def create_page(self, **datos):
        if datos["path"] == self.falla_en:
            raise RuntimeError("permiso denegado")
        self.creadas.append(datos["path"])

    def update_page(self, page_id, **datos):
        self.actualizadas.append(page_id)

    def delete_page(self, page_id):
        self.borradas.append(page_id)

def _cfg(docs):
    """Crea una Config de prueba apuntando a una carpeta temporal."""
    return Config(
        base_path="pruebas/redes",
        docs_dir=str(docs),
        locale="es",
        tag="gitlab-sync",
        locales=["es"],
        source_url="",
        wiki_url="http://fake",
        wiki_token="fake-token",
    )

# --- Error 1: prune no borra páginas de otra rama ---
def test_prune_no_borra_otra_rama_con_mismo_prefijo(tmp_path):
    (tmp_path / "a.md").write_text("# A\n", encoding="utf-8")
    ajena = {
        "id": 99, "path": "pruebas/redes-antiguo/guia", "locale": "es",
        "title": "G", "tags": ["gitlab-sync"],
    }
    cliente = ClienteFalso([ajena])
    sync(cliente, _cfg(tmp_path), prune=True)
    assert cliente.borradas == []

def test_prune_no_borra_paginas_sin_nuestro_tag(tmp_path):
    (tmp_path / "a.md").write_text("# A\n", encoding="utf-8")
    manual = {
        "id": 12, "path": "pruebas/redes/manual", "locale": "es",
        "title": "M", "tags": ["otra"],
    }
    cliente = ClienteFalso([manual])
    sync(cliente, _cfg(tmp_path), prune=True)
    assert cliente.borradas == []

def test_prune_borra_huerfana_propia(tmp_path):
    (tmp_path / "a.md").write_text("# A\n", encoding="utf-8")
    huerfana = {
        "id": 7, "path": "pruebas/redes/vieja", "locale": "es",
        "title": "V", "tags": ["gitlab-sync"],
    }
    cliente = ClienteFalso([huerfana])
    sync(cliente, _cfg(tmp_path), prune=True)
    assert cliente.borradas == [7]

# --- Error 3: un error no detiene el resto ---
def test_un_error_no_detiene_el_resto(tmp_path):
    (tmp_path / "a.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("# B\n", encoding="utf-8")
    cliente = ClienteFalso([], falla_en="pruebas/redes/a")
    resumen = sync(cliente, _cfg(tmp_path))
    assert cliente.creadas == ["pruebas/redes/b"]
    assert len(resumen["errores"]) == 1
