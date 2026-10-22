import requests

class WikiJsClient:
    """Cliente mínimo para la API GraphQL de Wiki.js."""

    def __init__(self, url, token):
        # /graphql es el único endpoint de la API de Wiki.js
        self.endpoint = url.rstrip("/") + "/graphql"
        self.headers = {"Authorization": f"Bearer {token}"}

    def _run(self, query, variables=None):
        """Envía una query/mutation y devuelve el campo 'data'.

        Centraliza aquí el manejo de errores para no repetirlo
        en cada método público.
        """
        resp = requests.post(
            self.endpoint,
            json={"query": query, "variables": variables or {}},
            headers=self.headers,
            timeout=30,
        )
        # Error de transporte HTTP (404, 500, etc.)
        resp.raise_for_status()
        data = resp.json()
        # GraphQL puede devolver HTTP 200 y aun así traer errores
        if "errors" in data:
            raise RuntimeError(data["errors"])
        return data["data"]

    def list_pages(self):
        """Lista todas las páginas de la wiki."""
        query = "{ pages { list { id path locale title tags } } }"
        return self._run(query)["pages"]["list"]

    def get_page(self, page_id):
        """Devuelve el contenido actual de una página por su id.

        Hace falta para comparar y decidir si una página cambió.
        """
        query = """
        query ($id: Int!) {
          pages {
            single(id: $id) {
              id path locale title description content tags { tag }
            }
          }
        }"""
        return self._run(query, {"id": page_id})["pages"]["single"]

    def create_page(self, path, title, content, description="", tags=None, locale="es"):
        """Crea una página nueva. Devuelve el id de la página creada."""
        query = """
        mutation ($content: String!, $description: String!, $path: String!,
                  $title: String!, $tags: [String]!, $locale: String!) {
          pages {
            create(content: $content, description: $description,
                   editor: "markdown", isPublished: true, isPrivate: false,
                   locale: $locale, path: $path, tags: $tags, title: $title) {
              responseResult { succeeded errorCode message }
              page { id }
            }
          }
        }"""
        data = self._run(query, {
            "content": content, "description": description,
            "path": path, "title": title,
            "tags": tags or [], "locale": locale,
        })
        result = data["pages"]["create"]["responseResult"]
        # Un fallo de la aplicación (p.ej. permisos) llega con HTTP 200,
        # por eso hay que mirar 'succeeded' y no solo el código HTTP.
        if not result["succeeded"]:
            raise RuntimeError(result["message"])
        return data["pages"]["create"]["page"]["id"]

    def update_page(self, page_id, path, title, content, description="", tags=None, locale="es"):
        """Actualiza una página existente. Hay que reenviar todos los campos."""
        query = """
        mutation ($id: Int!, $content: String!, $description: String!, $path: String!,
                  $title: String!, $tags: [String]!, $locale: String!) {
          pages {
            update(id: $id, content: $content, description: $description,
                   editor: "markdown", isPublished: true, isPrivate: false,
                   locale: $locale, path: $path, tags: $tags, title: $title) {
              responseResult { succeeded errorCode message }
              page { id }
            }
          }
        }"""
        data = self._run(query, {
            "id": page_id, "content": content, "description": description,
            "path": path, "title": title,
            "tags": tags or [], "locale": locale,
        })
        result = data["pages"]["update"]["responseResult"]
        if not result["succeeded"]:
            raise RuntimeError(result["message"])
        return data["pages"]["update"]["page"]["id"]

    def delete_page(self, page_id):
        """Borra una página por su id."""
        query = """
        mutation ($id: Int!) {
          pages {
            delete(id: $id) {
              responseResult { succeeded errorCode message }
            }
          }
        }"""
        data = self._run(query, {"id": page_id})
        result = data["pages"]["delete"]["responseResult"]
        if not result["succeeded"]:
            raise RuntimeError(result["message"])
