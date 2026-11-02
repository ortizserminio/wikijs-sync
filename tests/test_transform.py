from wikijs_sync.transform import split_front_matter


def test_sin_front_matter():
    texto = "# Solo contenido\n\nsin metadatos"
    meta, contenido = split_front_matter(texto)
    assert meta == {}
    assert contenido == texto


def test_front_matter_basico():
    texto = "---\ntitle: Hola\ndescription: Una prueba\n---\n# Cuerpo\n\ntexto"
    meta, contenido = split_front_matter(texto)
    assert meta["title"] == "Hola"
    assert meta["description"] == "Una prueba"
    assert contenido == "# Cuerpo\n\ntexto"


def test_front_matter_con_tags_lista():
    texto = "---\ntitle: X\ntags: [a, b, c]\n---\ncuerpo"
    meta, contenido = split_front_matter(texto)
    assert meta["tags"] == ["a", "b", "c"]
    assert contenido == "cuerpo"


def test_apertura_sin_cierre_no_es_front_matter():
    # '---' al inicio pero sin cierre: no debe tratarse como front matter
    texto = "---\ntitle: roto\nsin cierre"
    meta, contenido = split_front_matter(texto)
    assert meta == {}
    assert contenido == texto


from wikijs_sync.transform import rewrite_links, add_notice
from wikijs_sync.scanner import compute_path


def test_enlace_relativo_mismo_nivel():
    content = "Mira los [requisitos](requisitos.md)."
    out = rewrite_links(content, "instalacion/guia.md", compute_path, "pruebas")
    assert "(/pruebas/instalacion/requisitos)" in out


def test_enlace_relativo_carpeta_superior():
    content = "Vuelve al [inicio](../index.md)."
    out = rewrite_links(content, "instalacion/guia.md", compute_path, "pruebas")
    assert "(/pruebas)" in out


def test_enlace_con_ancla():
    content = "Ver [sección](requisitos.md#docker)."
    out = rewrite_links(content, "instalacion/guia.md", compute_path, "pruebas")
    assert "(/pruebas/instalacion/requisitos#docker)" in out


def test_enlace_externo_no_se_toca():
    content = "Ver [web](https://ejemplo.com/pagina.md)."
    out = rewrite_links(content, "guia.md", compute_path, "pruebas")
    assert "https://ejemplo.com/pagina.md" in out


def test_enlace_no_md_no_se_toca():
    content = "Una [imagen](foto.png)."
    out = rewrite_links(content, "guia.md", compute_path, "pruebas")
    assert "(foto.png)" in out


def test_aviso_se_antepone():
    out = add_notice("# Título\n\ncuerpo")
    assert out.startswith(">")
    assert "# Título" in out


def test_enlace_roto_se_detecta():
    # 'otro.md' NO está en known_files -> debe marcarse como roto
    known = {"guia.md"}  # solo existe guia.md
    rotos = []
    content = "Ver [otro](otro.md)."
    rewrite_links(content, "guia.md", compute_path, "pruebas",
                  known_files=known, broken=rotos)
    assert rotos == [("guia.md", "otro.md")]


def test_enlace_valido_no_se_marca_roto():
    # 'requisitos.md' SÍ existe -> no debe marcarse como roto
    known = {"guia.md", "requisitos.md"}
    rotos = []
    content = "Ver [reqs](requisitos.md)."
    rewrite_links(content, "guia.md", compute_path, "pruebas",
                  known_files=known, broken=rotos)
    assert rotos == []


def test_sin_known_files_no_detecta_rotos():
    # Si no se pasa known_files, no se detectan rotos (compatibilidad hacia atrás)
    rotos = []
    content = "Ver [otro](otro.md)."
    out = rewrite_links(content, "guia.md", compute_path, "pruebas", broken=rotos)
    assert rotos == []
    assert "(/pruebas/otro)" in out   # el enlace se reescribe igual


from wikijs_sync.transform import rewrite_images


def test_imagen_externa_no_se_toca():
    # Una imagen con URL http no se sube ni se reescribe
    subidas = []
    content = "![foto](https://ejemplo.com/foto.png)"
    out = rewrite_images(content, "guia.md", "/tmp/docs",
                         upload=lambda ruta, nombre: subidas.append(nombre) or nombre)
    assert out == content
    assert subidas == []


def test_imagen_inexistente_no_se_toca():
    # Si el fichero de imagen no existe en disco, se deja el enlace tal cual
    subidas = []
    content = "![foto](no-existe.png)"
    out = rewrite_images(content, "guia.md", "/tmp/docs-que-no-existe",
                         upload=lambda ruta, nombre: subidas.append(nombre) or nombre)
    assert out == content
    assert subidas == []


def test_imagen_local_se_sube_y_reescribe(tmp_path):
    # Creamos una imagen de verdad en un docs temporal y comprobamos que se "sube"
    # (con una función falsa) y que la ruta se reescribe a /<nombre>.
    docs = tmp_path
    (docs / "logo.png").write_bytes(b"fake-image-bytes")
    subidas = []
    content = "Mira el ![logo](logo.png) del proyecto."
    out = rewrite_images(content, "guia.md", str(docs),
                         upload=lambda ruta, nombre: subidas.append(nombre) or nombre)
    assert "![logo](/logo.png)" in out
    assert subidas == ["logo.png"]

def test_aviso_con_enlace_al_origen():
    url = "https://gitlab.umh.es/sistemas/redes/-/blob/master/docs/guia.md"
    resultado = add_notice("# Hola", url)
    assert resultado.startswith("> Esta página se genera automáticamente")
    assert f"[guia.md]({url})" in resultado
    assert resultado.endswith("# Hola")


# --- Test para Error 4: enlaces en bloques de código no se tocan ---
def test_enlace_en_bloque_codigo_no_se_toca():
    """Los enlaces dentro de bloques ``` no deben reescribirse."""
    contenido = """# Ejemplo

Aquí un enlace normal: [guía](guia.md)

```markdown
[ejemplo](otro.md)
```

Y código inline: `[no tocar](esto.md)` tampoco.
"""
    resultado = rewrite_links(
        contenido, "doc.md", lambda p, b: f"{b}/{p.replace('.md','')}", "base"
    )
    # El enlace normal SÍ se reescribe
    assert "[guía](/base/guia)" in resultado
    # El enlace dentro de ``` NO se toca
    assert "[ejemplo](otro.md)" in resultado
    # El enlace inline tampoco
    assert "`[no tocar](esto.md)`" in resultado


def test_imagen_en_bloque_codigo_no_se_toca(tmp_path):
    """Las imágenes dentro de bloques ``` no deben reescribirse."""
    # Crear imagen real
    (tmp_path / "logo.png").write_bytes(b"PNG fake")
    
    contenido = """# Ejemplo

Imagen real: ![logo](logo.png)

```markdown
![ejemplo](otra.png)
```
"""
    subidas = []
    def fake_upload(ruta, nombre):
        subidas.append(nombre)
        return "uploaded-" + nombre
    
    resultado = rewrite_images(contenido, "doc.md", tmp_path, fake_upload)
    
    # La imagen real SÍ se sube y reescribe
    assert "![logo](/uploaded-logo.png)" in resultado
    # La imagen dentro de ``` NO se toca
    assert "![ejemplo](otra.png)" in resultado
    # Solo se subió una imagen
    assert len(subidas) == 1
