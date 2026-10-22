"""Script suelto para probar el WikiJsClient contra la wiki local.

Lee la URL y el token de las variables de entorno WIKI_URL y WIKI_TOKEN.
Ejecuta el ciclo completo: crear -> leer -> actualizar -> borrar.
"""
import os

from wikijs_sync.wikijs import WikiJsClient

url = os.environ["WIKI_URL"]
token = os.environ["WIKI_TOKEN"]
client = WikiJsClient(url, token)

print("== Páginas actuales ==")
for p in client.list_pages():
    print(f"  [{p['id']}] {p['path']}  ({p['title']})")

print("\n== Crear ==")
page_id = client.create_page(
    path="pruebas/cliente",
    title="Prueba del cliente",
    content="# Hola\n\nCreada desde el WikiJsClient.",
    description="Página de prueba",
    tags=["gitlab-sync"],
)
print(f"  Creada con id {page_id}")

print("\n== Leer ==")
page = client.get_page(page_id)
print(f"  título: {page['title']}")
print(f"  contenido: {page['content']!r}")

print("\n== Actualizar ==")
client.update_page(
    page_id,
    path="pruebas/cliente",
    title="Prueba del cliente (editada)",
    content="# Hola otra vez\n\nContenido actualizado.",
    description="Página de prueba",
    tags=["gitlab-sync"],
)
print("  Actualizada")

print("\n== Borrar ==")
client.delete_page(page_id)
print("  Borrada")

print("\nTodo OK")
