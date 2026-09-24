from decimal import Decimal

from src.modules.contadores.domain.services.estimacion.aritmetica_decimal_cs import dividir
from src.modules.contadores.domain.services.estimacion.redondeo import a_decimal
from src.modules.contadores.domain.value_objects.estimacion.estado_maquina import Tecnologia
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput

_VELOCIDAD_DEFAULT_PPM: dict[Tecnologia, float] = {"MONO": 45.0, "COLOR": 25.0}
_MINUTOS_POR_JORNADA = Decimal(60 * 8)


def velocidad_efectiva(tecnologia: Tecnologia, velocidad_ppm: float | None) -> float:
    """`VelocidadEfectiva` del legacy: sin velocidad cargada o cargada en 0/1
    (error de carga común) se asume el default por tecnología."""
    if velocidad_ppm is None or velocidad_ppm <= 1:
        return _VELOCIDAD_DEFAULT_PPM[tecnologia]
    return velocidad_ppm


def hay_salto_imposible(impresiones: float | None, entrada: EstimacionInput) -> bool:
    """`DetectarSaltoImposible` del legacy: impresiones por día del período
    por encima de lo que el equipo puede imprimir en una jornada de 8 h. Solo
    se evalúa con impresiones positivas."""
    if impresiones is None or impresiones <= 0:
        return False
    dias_periodo = (entrada.periodo_hasta - entrada.periodo_desde).days
    if dias_periodo <= 0:
        return False
    velocidad = a_decimal(velocidad_efectiva(entrada.tecnologia, entrada.velocidad_ppm))
    return dividir(a_decimal(impresiones), dias_periodo) > velocidad * _MINUTOS_POR_JORNADA
