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
