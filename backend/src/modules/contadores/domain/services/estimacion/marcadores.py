from dataclasses import replace

from src.modules.contadores.domain.services.estimacion.antiguedad import historia_en_alerta
from src.modules.contadores.domain.services.estimacion.coloreo import resolver_coloreo
from src.modules.contadores.domain.services.estimacion.salto_imposible import hay_salto_imposible
from src.modules.contadores.domain.services.estimacion.semaforo import resolver_semaforo
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)


def finalizar(borrador: EstimacionResultado, entrada: EstimacionInput) -> EstimacionResultado:
    """Lo que el legacy agrega a toda estimación de una fila pendiente, sea
    cual sea la rama: `MesesSinRealEnAlerta` y `AplicarMarcadores` (salto
    imposible, coloreo y semáforo, en ese orden porque el semáforo depende
    de los otros dos). Los valores de esos campos en `borrador` se pisan.
    Una fila ya real (que solo llega acá forzada o con P/L manual) queda
    siempre VERDE, como en `CalcularSemaforo`."""
    en_alerta = historia_en_alerta(entrada.ultimo_real, entrada.tecnologia, entrada.fecha_objetivo)
    con_bordes = replace(
        borrador,
        meses_sin_real_en_alerta=en_alerta,
        borde_salto_imposible=hay_salto_imposible(borrador.impresiones, entrada),
        coloreo=resolver_coloreo(borrador, entrada.prom_6_facturados),
    )
    if not entrada.pendiente_estimar:
        return replace(con_bordes, semaforo="VERDE")
    return replace(con_bordes, semaforo=resolver_semaforo(con_bordes, entrada.t4_revisado))
