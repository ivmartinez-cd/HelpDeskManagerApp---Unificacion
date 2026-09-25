import pytest

from src.modules.reporte_incidentes.application.use_cases.gestionar_tipificacion import (
    Correccion,
    CorregirTipificacion,
    EliminarCategoria,
    GuardarCategoria,
)
from src.modules.reporte_incidentes.domain.entities.categoria import Categoria
from src.modules.reporte_incidentes.domain.errors import (
    CategoriaInvalidaError,
    CategoriaNoEncontradaError,
    TipificacionInvalidaError,
)
from tests.unit.application.reporte_incidentes.fakes import FakeCache, FakeTaxonomia

_NUEVA = Categoria(" Red ", "#123abc", " pauta ", ("IP", " IP ", "", "Cable"))


async def test_la_correccion_se_guarda_con_confianza_alta_bajo_la_clave_del_caso() -> None:
    cache = FakeCache()
    uso = CorregirTipificacion(FakeTaxonomia(), cache)  # type: ignore[arg-type]
    await uso.execute(Correccion("atasco", None, "limpieza", "Medio de Impresion",
                                 "Atasco de papel (comun)"))
    guardada = cache.guardadas["atasco||limpieza"]
    assert (guardada.subcategoria, guardada.confianza) == ("Atasco de papel (comun)", "alta")


@pytest.mark.parametrize(("categoria", "subcategoria"), [
    ("Inventada", "x"), ("Medio de Impresion", "Inventada"),
])
async def test_la_correccion_valida_contra_la_taxonomia(categoria: str, subcategoria: str) -> None:
    uso = CorregirTipificacion(FakeTaxonomia(), FakeCache())  # type: ignore[arg-type]
    with pytest.raises(TipificacionInvalidaError):
        await uso.execute(Correccion("a", None, None, categoria, subcategoria))


async def test_crear_categoria_normaliza_nombre_y_subcategorias() -> None:
    taxonomia = FakeTaxonomia()
    await GuardarCategoria(taxonomia).execute(_NUEVA, nombre_anterior=None)  # type: ignore[arg-type]
    assert taxonomia.categorias[-1] == Categoria("Red", "#123abc", "pauta", ("IP", "Cable"))


async def test_nombre_duplicado_sin_distinguir_mayusculas_se_rechaza() -> None:
    duplicada = Categoria("MEDIO DE IMPRESION", "#123abc", "pauta", ())
    with pytest.raises(CategoriaInvalidaError, match="Ya existe"):
        await GuardarCategoria(FakeTaxonomia()).execute(duplicada, None)  # type: ignore[arg-type]


async def test_editar_conservando_el_nombre_no_cuenta_como_duplicado() -> None:
    taxonomia = FakeTaxonomia()
    editada = Categoria("Medio de Impresion", "#000000", "nueva pauta", ("Atasco",))
    await GuardarCategoria(taxonomia).execute(editada, "medio de impresion")  # type: ignore[arg-type]
    assert taxonomia.categorias == [editada]


@pytest.mark.parametrize("invalida", [
    Categoria("", "#123abc", "pauta", ()),
    Categoria("Red", "#123abc", "  ", ()),
    Categoria("Red", "azul", "pauta", ()),
])
async def test_valida_nombre_pauta_y_color(invalida: Categoria) -> None:
    with pytest.raises(CategoriaInvalidaError):
        await GuardarCategoria(FakeTaxonomia()).execute(invalida, None)  # type: ignore[arg-type]


async def test_editar_o_eliminar_una_categoria_inexistente_da_no_encontrada() -> None:
    with pytest.raises(CategoriaNoEncontradaError):
        await GuardarCategoria(FakeTaxonomia()).execute(_NUEVA, "no existe")  # type: ignore[arg-type]
    with pytest.raises(CategoriaNoEncontradaError):
        await EliminarCategoria(FakeTaxonomia()).execute("no existe")  # type: ignore[arg-type]
