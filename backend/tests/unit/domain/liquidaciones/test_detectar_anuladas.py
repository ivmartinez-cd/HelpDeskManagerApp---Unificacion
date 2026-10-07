"""detectar_anuladas: diff puro de liquidaciones locales pendientes que AyC ya no
reporta como vigentes — los dos comportamientos posibles de AyC (omitir la
anulada, o incluirla con estado explícito) y el guard contra SOAP vacío."""

from datetime import date

from src.modules.liquidaciones.domain.services.detectar_anuladas import detectar_anuladas
from src.modules.liquidaciones.domain.services.numeracion_ayc import numero_liquidacion
from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import CdLiquidacion
from tests.unit.domain.liquidaciones.factories import make_liquidacion


def _cd_liq(ayc_id: int, *, estado: str = "Recibida") -> CdLiquidacion:
    return CdLiquidacion(
        id=ayc_id,
        prestador_cd_id=1310,
        numero_liquidacion=numero_liquidacion(ayc_id),
        fecha_liquidacion=date(2026, 8, 1),
        estado=estado,
        cant_incidentes=1,
    )


def test_soap_vacio_no_detecta_nada() -> None:
    local = make_liquidacion(numero_liquidacion=numero_liquidacion(1))

    assert detectar_anuladas([], [local]) == []


def test_local_ausente_del_listado_se_detecta_anulada() -> None:
    local = make_liquidacion(numero_liquidacion=numero_liquidacion(1))
    otra_vigente = make_liquidacion(numero_liquidacion=numero_liquidacion(2))

    resultado = detectar_anuladas([_cd_liq(2)], [local, otra_vigente])

    assert resultado == [local]


def test_local_con_estado_explicito_anulado_se_detecta() -> None:
    local = make_liquidacion(numero_liquidacion=numero_liquidacion(1))

    resultado = detectar_anuladas([_cd_liq(1, estado="Anulada")], [local])

    assert resultado == [local]


def test_local_mas_vieja_que_el_top_n_lleno_no_se_toca() -> None:
    """AyC devuelve las N más nuevas: si el listado llenó el `Top`, un local con
    ID < el mínimo puede estar fuera del window — no hay evidencia de anulación."""
    local_fuera_de_ventana = make_liquidacion(numero_liquidacion=numero_liquidacion(1))

    resultado = detectar_anuladas([_cd_liq(5), _cd_liq(4)], [local_fuera_de_ventana], top=2)

    assert resultado == []


def test_local_mas_nueva_que_todas_las_vigentes_se_detecta() -> None:
    """Caso 3993-2 (TUCUMAN, 2026-10-07): anulada en AyC con ID mayor a todas las
    que siguen vigentes — antes quedaba fuera del window y no se borraba nunca."""
    local = make_liquidacion(numero_liquidacion=numero_liquidacion(3993))

    resultado = detectar_anuladas([_cd_liq(3989), _cd_liq(3988)], [local])

    assert resultado == [local]


def test_local_vigente_no_se_toca() -> None:
    local = make_liquidacion(numero_liquidacion=numero_liquidacion(1))

    resultado = detectar_anuladas([_cd_liq(1)], [local])

    assert resultado == []
