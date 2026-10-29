import requests

class WikiJsClient:
    """Cliente mínimo para la API GraphQL de Wiki.js."""

    def __init__(self, url, token):
        self.base_url = url.rstrip("/")
        # /graphql es el endpoint de la API GraphQL (páginas)
        self.endpoint = self.base_url + "/graphql"
        # /u es el endpoint REST para SUBIR ficheros (las imágenes no van por GraphQL)
        self.upload_endpoint = self.base_url + "/u"
        self.token = token
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

    def upload_asset(self, file_path, filename=None, folder_id=0):
        """Sube un fichero (imagen) a Wiki.js por el endpoint REST /u.

        Las imágenes NO se suben por GraphQL, sino con un POST multipart a /u.
        El formulario lleva DOS campos, ambos llamados 'mediaUpload':
          1) un JSON con el folderId (carpeta de destino; 0 = raíz)
          2) el fichero binario
        (Formato descubierto espiando la petición del editor de la propia wiki.)
        """
        import json
        import os

        if filename is None:
            filename = os.path.basename(file_path)

        with open(file_path, "rb") as f:
            files = [
                # Primer campo: el JSON con el folderId.
                ("mediaUpload", (None, json.dumps({"folderId": folder_id}), "application/json")),
                # Segundo campo: el fichero en sí.
                ("mediaUpload", (filename, f, "application/octet-stream")),
            ]
            resp = requests.post(
                self.upload_endpoint,
                files=files,
                headers=self.headers,   # solo el Authorization; requests pone el multipart
                timeout=60,
            )
        resp.raise_for_status()
        return resp.status_code == 200

    def list_asset_names(self, folder_id=0):
        """Nombres de los ficheros de una carpeta de assets (0 = raíz)."""
        query = """
        query ($folderId: Int!) {
          assets { list(folderId: $folderId, kind: ALL) { filename } }
        }"""
        datos = self._run(query, {"folderId": folder_id})
        return {a["filename"] for a in datos["assets"]["list"]}

