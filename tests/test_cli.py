"""Tests para el punto de entrada de línea de comandos."""
from unittest.mock import patch

import pytest

from wikijs_sync.cli import main


@pytest.fixture
def env_vars(monkeypatch):
    """Configura las variables de entorno necesarias."""
    monkeypatch.setenv("WIKI_URL", "http://localhost:3000")
    monkeypatch.setenv("WIKI_TOKEN", "test-token")


def test_cli_help():
    """--help muestra la ayuda y sale con código 0."""
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0


def test_cli_config_no_existe():
    """Sale con código 2 si el fichero de configuración no existe."""
    result = main(["--config", "no-existe-este-fichero.yml"])
    assert result == 2


def test_cli_falta_variables_entorno(tmp_path, monkeypatch):
    """Sale con código 2 si faltan las variables de entorno."""
    monkeypatch.delenv("WIKI_URL", raising=False)
    monkeypatch.delenv("WIKI_TOKEN", raising=False)

    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("""
base_path: pruebas
docs_dir: docs
""")

    result = main(["--config", str(cfg_file)])
    assert result == 2


def test_cli_parsea_argumentos(tmp_path, env_vars):
    """Parsea correctamente --dry-run y --prune."""
    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("""
base_path: pruebas
docs_dir: docs
""")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Test\n")

    # Mock del cliente y sync para no hacer llamadas reales
    with patch("wikijs_sync.cli.WikiJsClient"), \
         patch("wikijs_sync.cli.sync") as mock_sync:

        mock_sync.return_value = {"errores": [], "creadas": 0, "actualizadas": 0, "borradas": 0}

        result = main(["--config", str(cfg_file), "--dry-run", "--prune"])

        # Verifica que sync se llamó con dry_run=True y prune=True
        mock_sync.assert_called_once()
        call_kwargs = mock_sync.call_args[1]
        assert call_kwargs["dry_run"] is True
        assert call_kwargs["prune"] is True
        assert result == 0


def test_cli_error_en_sync(tmp_path, env_vars):
    """Sale con código 1 si sync lanza una excepción."""
    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("""
base_path: pruebas
docs_dir: docs
""")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Test\n")

    with patch("wikijs_sync.cli.WikiJsClient"), \
         patch("wikijs_sync.cli.sync") as mock_sync:

        mock_sync.side_effect = RuntimeError("Wiki no responde")

        result = main(["--config", str(cfg_file)])
        assert result == 1


def test_cli_errores_parciales(tmp_path, env_vars):
    """Sale con código 1 si hay errores parciales en sync."""
    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("""
base_path: pruebas
docs_dir: docs
""")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Test\n")

    with patch("wikijs_sync.cli.WikiJsClient"), \
         patch("wikijs_sync.cli.sync") as mock_sync:

        # Simula que hubo un error en una página
        mock_sync.return_value = {
            "errores": [("pruebas/pagina", "permiso denegado")],
            "creadas": 1, "actualizadas": 0, "borradas": 0
        }

        result = main(["--config", str(cfg_file)])
        assert result == 1


def test_cli_exito(tmp_path, env_vars):
    """Sale con código 0 si todo va bien."""
    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("""
base_path: pruebas
docs_dir: docs
""")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Test\n")

    with patch("wikijs_sync.cli.WikiJsClient"), \
         patch("wikijs_sync.cli.sync") as mock_sync:

        mock_sync.return_value = {
            "errores": [],
            "creadas": 1, "actualizadas": 0, "borradas": 0, "sin_cambios": 0
        }

        result = main(["--config", str(cfg_file)])
        assert result == 0



# --- Test para Error 15: --strict falla si hay enlaces rotos ---
def test_cli_strict_falla_con_enlaces_rotos(tmp_path, env_vars):
    """Con --strict, sale con código 1 si hay enlaces rotos."""
    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("""
base_path: pruebas
docs_dir: docs
""")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Test\n")

    with patch("wikijs_sync.cli.WikiJsClient"), \
         patch("wikijs_sync.cli.sync") as mock_sync:

        # Simula que sync detectó enlaces rotos
        mock_sync.return_value = {
            "errores": [],
            "creadas": 1, "actualizadas": 0, "borradas": 0, "sin_cambios": 0,
            "enlaces_rotos": [("a.md", "no-existe.md")],
        }

        result = main(["--config", str(cfg_file), "--strict"])
        assert result == 1


def test_cli_sin_strict_avisa_pero_no_falla(tmp_path, env_vars):
    """Sin --strict, los enlaces rotos no hacen fallar (solo aviso)."""
    cfg_file = tmp_path / "wikijs-sync.yml"
    cfg_file.write_text("""
base_path: pruebas
docs_dir: docs
""")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("# Test\n")

    with patch("wikijs_sync.cli.WikiJsClient"), \
         patch("wikijs_sync.cli.sync") as mock_sync:

        mock_sync.return_value = {
            "errores": [],
            "creadas": 1, "actualizadas": 0, "borradas": 0, "sin_cambios": 0,
            "enlaces_rotos": [("a.md", "no-existe.md")],
        }

        # Sin --strict, debe salir con 0
        result = main(["--config", str(cfg_file)])
        assert result == 0
