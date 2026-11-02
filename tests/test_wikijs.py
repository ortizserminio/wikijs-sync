"""Tests para el cliente de la API de Wiki.js."""
from unittest.mock import MagicMock, patch

import pytest

from wikijs_sync.wikijs import WikiJsClient


@pytest.fixture
def client():
    """Cliente configurado para tests."""
    return WikiJsClient("http://localhost:3000", "test-token")


def test_client_init():
    """El cliente se inicializa correctamente."""
    c = WikiJsClient("http://localhost:3000/", "my-token")
    assert c.base_url == "http://localhost:3000"
    assert c.endpoint == "http://localhost:3000/graphql"
    assert c.upload_endpoint == "http://localhost:3000/u"
    assert c.token == "my-token"
    assert c.headers["Authorization"] == "Bearer my-token"


def test_run_success(client):
    """_run devuelve los datos cuando la respuesta es correcta."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {"pages": {"list": [{"id": 1, "title": "Test"}]}}
    }

    with patch("requests.post", return_value=mock_response) as mock_post:
        result = client._run("{ pages { list { id title } } }")

        assert result == {"pages": {"list": [{"id": 1, "title": "Test"}]}}
        mock_post.assert_called_once()


def test_run_graphql_error(client):
    """_run lanza RuntimeError si la respuesta contiene errores GraphQL."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "errors": [{"message": "Query inválida"}]
    }

    with patch("requests.post", return_value=mock_response):
        with pytest.raises(RuntimeError) as exc:
            client._run("{ invalid }")

        assert "Query inválida" in str(exc.value)


def test_run_http_error(client):
    """_run lanza excepción si hay error HTTP."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("404 Not Found")

    with patch("requests.post", return_value=mock_response):
        with pytest.raises(Exception) as exc:
            client._run("{ pages { list { id } } }")

        assert "404" in str(exc.value)


def test_list_pages(client):
    """list_pages devuelve la lista de páginas."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "pages": {
                "list": [
                    {"id": 1, "path": "test", "locale": "es", "title": "Test", "tags": []},
                    {"id": 2, "path": "otro", "locale": "es", "title": "Otro", "tags": ["tag1"]},
                ]
            }
        }
    }

    with patch("requests.post", return_value=mock_response):
        pages = client.list_pages()

        assert len(pages) == 2
        assert pages[0]["id"] == 1
        assert pages[1]["path"] == "otro"


def test_get_page(client):
    """get_page devuelve los detalles de una página."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "pages": {
                "single": {
                    "id": 1, "path": "test", "locale": "es",
                    "title": "Test", "description": "Desc",
                    "content": "# Contenido", "tags": [{"tag": "t1"}]
                }
            }
        }
    }

    with patch("requests.post", return_value=mock_response):
        page = client.get_page(1)

        assert page["id"] == 1
        assert page["content"] == "# Contenido"


def test_create_page_success(client):
    """create_page devuelve el id de la página creada."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "pages": {
                "create": {
                    "responseResult": {"succeeded": True, "errorCode": None, "message": None},
                    "page": {"id": 42}
                }
            }
        }
    }

    with patch("requests.post", return_value=mock_response):
        page_id = client.create_page(
            path="nuevo", title="Nuevo", content="# Hola"
        )

        assert page_id == 42


def test_create_page_error(client):
    """create_page lanza RuntimeError si la operación falla."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "pages": {
                "create": {
                    "responseResult": {
                        "succeeded": False,
                        "errorCode": "PERMISSION_DENIED",
                        "message": "No tienes permisos"
                    },
                    "page": None
                }
            }
        }
    }

    with patch("requests.post", return_value=mock_response):
        with pytest.raises(RuntimeError) as exc:
            client.create_page(path="nuevo", title="Nuevo", content="# Hola")

        assert "No tienes permisos" in str(exc.value)


def test_update_page_success(client):
    """update_page devuelve el id de la página actualizada."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "pages": {
                "update": {
                    "responseResult": {"succeeded": True, "errorCode": None, "message": None},
                    "page": {"id": 10}
                }
            }
        }
    }

    with patch("requests.post", return_value=mock_response):
        page_id = client.update_page(
            page_id=10, path="existente", title="Actualizado", content="# Nuevo"
        )

        assert page_id == 10


def test_delete_page_success(client):
    """delete_page no lanza excepción si la operación tiene éxito."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "pages": {
                "delete": {
                    "responseResult": {"succeeded": True, "errorCode": None, "message": None}
                }
            }
        }
    }

    with patch("requests.post", return_value=mock_response):
        # No debe lanzar excepción
        client.delete_page(10)


def test_delete_page_error(client):
    """delete_page lanza RuntimeError si la operación falla."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "pages": {
                "delete": {
                    "responseResult": {
                        "succeeded": False,
                        "errorCode": "PAGE_NOT_FOUND",
                        "message": "La página no existe"
                    }
                }
            }
        }
    }

    with patch("requests.post", return_value=mock_response):
        with pytest.raises(RuntimeError) as exc:
            client.delete_page(999)

        assert "La página no existe" in str(exc.value)


def test_list_asset_names(client):
    """list_asset_names devuelve un conjunto de nombres de fichero."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "assets": {
                "list": [
                    {"filename": "logo.png"},
                    {"filename": "diagrama.svg"},
                ]
            }
        }
    }

    with patch("requests.post", return_value=mock_response):
        names = client.list_asset_names()

        assert names == {"logo.png", "diagrama.svg"}


def test_upload_asset(client, tmp_path):
    """upload_asset sube un fichero correctamente."""
    # Crear un fichero temporal
    img_file = tmp_path / "test.png"
    img_file.write_bytes(b"PNG fake content")

    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("requests.post", return_value=mock_response) as mock_post:
        result = client.upload_asset(str(img_file), "renamed.png")

        assert result is True
        mock_post.assert_called_once()
        # Verificar que se envió al endpoint correcto
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:3000/u"
