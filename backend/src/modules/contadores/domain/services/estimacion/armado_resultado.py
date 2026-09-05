from dataclasses import replace

from src.modules.contadores.domain.services.estimacion.marcadores import Marcadores
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)


def con_marcadores(resultado: EstimacionResultado, marcadores: Marcadores) -> EstimacionResultado:
    """Completa un `EstimacionResultado` ya armado por una rama de la
    cascada con los marcadores compartidos (§7): semáforo, coloreo y borde
    de salto imposible. Los valores de estos tres campos en `resultado` son
    placeholders — siempre se sobrescriben acá."""
    return replace(
        resultado,
        semaforo=marcadores.semaforo,
        coloreo=marcadores.coloreo,
        borde_salto_imposible=marcadores.borde_salto_imposible,
    )
