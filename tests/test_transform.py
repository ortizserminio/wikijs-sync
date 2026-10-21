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
