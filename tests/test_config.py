"""Tests para la carga de configuración."""
import pytest

from wikijs_sync.config import load_config


@pytest.fixture
def env_vars(monkeypatch):
    """Configura las variables de entorno necesarias."""
    monkeypatch.setenv("WIKI_URL", "http://localhost:3000")
    monkeypatch.setenv("WIKI_TOKEN", "test-token")


def test_config_basica(tmp_path, env_vars):
    """Carga una configuración mínima correctamente."""
    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("""
base_path: pruebas/redes
docs_dir: docs
""")
    cfg = load_config(str(cfg_file))

    assert cfg.base_path == "pruebas/redes"
    assert cfg.docs_dir == "docs"
    assert cfg.locale == "es"  # por defecto
    assert cfg.tag == "gitlab-sync:pruebas/redes"
    assert cfg.wiki_url == "http://localhost:3000"
    assert cfg.wiki_token == "test-token"


def test_config_con_todos_los_campos(tmp_path, env_vars):
    """Carga una configuración completa."""
    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("""
base_path: conocimiento/sistemas
docs_dir: documentacion
locale: ca
locales: [ca, es, va]
locale_map:
  va: ca
tag: mi-tag
source_url: https://gitlab.example.com/repo
""")
    cfg = load_config(str(cfg_file))

    assert cfg.base_path == "conocimiento/sistemas"
    assert cfg.docs_dir == "documentacion"
    assert cfg.locale == "ca"
    assert set(cfg.locales) == {"ca", "es", "va"}
    assert cfg.locale_map == {"va": "ca"}
    assert cfg.tag == "mi-tag:conocimiento/sistemas"
    assert cfg.source_url == "https://gitlab.example.com/repo"


def test_config_sin_variables_entorno(tmp_path, monkeypatch):
    """Falla si faltan las variables de entorno."""
    monkeypatch.delenv("WIKI_URL", raising=False)
    monkeypatch.delenv("WIKI_TOKEN", raising=False)

    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("""
base_path: pruebas
docs_dir: docs
""")

    with pytest.raises(RuntimeError) as exc:
        load_config(str(cfg_file))

    assert "WIKI_URL" in str(exc.value)


def test_config_sin_base_path(tmp_path, env_vars):
    """Falla con mensaje claro si falta base_path en el YAML."""
    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("""
docs_dir: docs
""")

    with pytest.raises(ValueError) as exc:
        load_config(str(cfg_file))

    assert "base_path" in str(exc.value)


def test_config_sin_docs_dir(tmp_path, env_vars):
    """Falla con mensaje claro si falta docs_dir en el YAML."""
    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("""
base_path: pruebas
""")

    with pytest.raises(ValueError) as exc:
        load_config(str(cfg_file))

    assert "docs_dir" in str(exc.value)


def test_config_yaml_vacio(tmp_path, env_vars):
    """Falla con mensaje claro con un YAML vacío."""
    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("")

    with pytest.raises(ValueError) as exc:
        load_config(str(cfg_file))

    assert "vacío" in str(exc.value)


def test_config_fichero_no_existe(env_vars):
    """Falla si el fichero de configuración no existe."""
    with pytest.raises(FileNotFoundError):
        load_config("no-existe.yml")


def test_config_avisa_claves_desconocidas(tmp_path, env_vars, capsys):
    """Avisa de claves desconocidas en el YAML."""
    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("""
base_path: pruebas
docs_dir: docs
clave_inventada: valor
otra_clave: otro
""")

    load_config(str(cfg_file))

    captured = capsys.readouterr()
    assert "clave_inventada" in captured.out
    assert "otra_clave" in captured.out


def test_config_normaliza_base_path(tmp_path, env_vars):
    """Quita barras del base_path."""
    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("""
base_path: /pruebas/redes/
docs_dir: docs
""")

    cfg = load_config(str(cfg_file))
    assert cfg.base_path == "pruebas/redes"


def test_config_locale_map_normaliza_a_minusculas(tmp_path, env_vars):
    """locale_map se normaliza a minúsculas."""
    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("""
base_path: pruebas
docs_dir: docs
locale_map:
  VA: CA
  EN: en
""")

    cfg = load_config(str(cfg_file))
    assert cfg.locale_map == {"va": "ca", "en": "en"}
