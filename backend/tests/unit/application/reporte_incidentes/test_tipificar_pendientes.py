import pytest

from src.modules.reporte_incidentes.application.use_cases.armar_reporte import PedidoReporte
from src.modules.reporte_incidentes.application.use_cases.tipificar_pendientes import (
    ConfigIA,
    TipificarPendientes,
)
from src.modules.reporte_incidentes.domain.entities.categoria import TipificacionGuardada
from src.modules.reporte_incidentes.domain.errors import IaNoConfiguradaError
from src.modules.reporte_incidentes.domain.services.tipificacion import PENDIENTE, clave_caso
from tests.unit.application.reporte_incidentes.fakes import (
    FakeArmar,
    FakeCache,
    FakeClasificador,
)
from tests.unit.domain.reporte_incidentes.fakes import incidente

_PEDIDO = PedidoReporte("1", "2026-06", 1)
_CONFIG = ConfigIA(
    lote=2, concurrencia=2, precio_entrada_por_millon=1.0, precio_salida_por_millon=10.0
)


def _pendiente(descripcion: str) -> object:
    return incidente(descripcion=descripcion, categoria=PENDIENTE, subcategoria="")


def _caso(incidentes, cache=None, ia=None):  # type: ignore[no-untyped-def]
    cache = cache or FakeCache()
    ia = ia or FakeClasificador()
    uso = TipificarPendientes(FakeArmar(incidentes), (cache, ia), _CONFIG)  # type: ignore[arg-type]
    return uso, cache, ia


async def test_tipifica_en_lotes_los_casos_distintos_y_los_guarda() -> None:
    incidentes = [_pendiente(d) for d in ("a", "b", "b", "c")]
    uso, cache, ia = _caso(incidentes)
    r = await uso.execute(_PEDIDO)
    assert (r.casos, r.tipificados, r.fallidos, r.llamadas) == (3, 3, 0, 2)
    assert len(ia.prompts) == 2  # lotes de 2: [a, b] y [c]
    assert r.costo_usd == pytest.approx((2000 * 1.0 + 200 * 10.0) / 1_000_000)
    assert cache.guardadas[clave_caso(incidentes[0])].categoria == "Medio de Impresion"


async def test_no_vuelve_a_mandar_casos_que_ya_tienen_tipificacion_guardada() -> None:
    media = _pendiente("dudoso")
    cache = FakeCache({clave_caso(media): TipificacionGuardada("X", "Y", "media")})
    uso, _, ia = _caso([media, incidente(descripcion="ya", categoria="Medio de Impresion")], cache)
    r = await uso.execute(_PEDIDO)
    assert (r.casos, r.llamadas, ia.prompts) == (0, 0, [])


async def test_si_la_ia_no_responde_el_lote_queda_pendiente_sin_guardar_nada() -> None:
    uso, cache, _ = _caso([_pendiente("a")], ia=FakeClasificador(falla=True))
    r = await uso.execute(_PEDIDO)
    assert (r.tipificados, r.fallidos) == (0, 1)
    assert cache.guardadas == {}


async def test_sin_clave_de_ia_avisa_en_vez_de_dejar_todo_pendiente_en_silencio() -> None:
    uso, _, _ = _caso([_pendiente("a")], ia=FakeClasificador(configurado=False))
    with pytest.raises(IaNoConfiguradaError):
        await uso.execute(_PEDIDO)
