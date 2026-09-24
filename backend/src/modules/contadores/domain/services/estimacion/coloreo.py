from decimal import Decimal

from src.modules.contadores.domain.services.estimacion.redondeo import a_decimal
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    Coloreo,
    FuenteEstimacion,
)

FACTOR_ALTO = Decimal("1.4")  # ColorearAlto_Factor
FACTOR_BAJO = Decimal("0.6")  # ColorearBajo_Factor
_FUENTES_SIN_COLOREO: tuple[FuenteEstimacion, ...] = ("Backup_SinST", "EnTransito")


def resolver_coloreo(
    resultado: EstimacionResultado, prom_6_facturados: float | None
) -> Coloreo:
    """`CalcularColoreo` del legacy: contra el promedio de impresiones de los
    últimos 6 procesos facturados. NORMAL cuando no hay impresiones, no hay
    promedio positivo, o es un equipo sin movimiento (Backup sin T4 / En
    tránsito: 0 impresiones ahí no es una anomalía)."""
    sin_referencia = prom_6_facturados is None or prom_6_facturados <= 0
    if resultado.impresiones is None or sin_referencia or resultado.fuente in _FUENTES_SIN_COLOREO:
        return "NORMAL"
    assert prom_6_facturados is not None
    impresiones = a_decimal(resultado.impresiones)
    promedio = a_decimal(prom_6_facturados)
    if impresiones > FACTOR_ALTO * promedio:
        return "AZUL"
    if impresiones < FACTOR_BAJO * promedio:
        return "NARANJA"
    return "NORMAL"
