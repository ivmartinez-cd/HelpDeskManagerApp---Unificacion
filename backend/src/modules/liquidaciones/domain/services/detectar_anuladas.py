"""Diff puro para el sync de CD: qué liquidaciones locales pendientes ya no son
vigentes en AyC — colaborador de `SincronizarLiquidaciones._detectar_y_eliminar_anuladas`.

Detecta dos comportamientos posibles de AyC:
- Que omita las anuladas del response (la más común): ausencia en `liqs`.
- Que las incluya con un estado explícito (ej. "Anulada"): campo `estado`.
"""

from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion
from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import CdLiquidacion

# Nombres de estado que AyC puede devolver para una liquidación anulada, en caso de que
# getTopLiquidations las incluya con estado explícito en lugar de omitirlas.
_ESTADOS_CD_ANULADOS = frozenset({"anulada", "anulado", "cancelada", "void", "voided"})


def detectar_anuladas(liqs: list[CdLiquidacion], locales: list[Liquidacion]) -> list[Liquidacion]:
    """Locales que AyC ya no reporta como vigentes — para que el caller las borre.

    `[]` si `liqs` está vacío (fallo de red u otro error) — evita eliminar
    falsamente todo el historial local del prestador ante un SOAP vacío.
    """
    if not liqs:
        return []

    cd_vigentes = {
        cd_liq.numero_liquidacion
        for cd_liq in liqs
        if cd_liq.estado.lower() not in _ESTADOS_CD_ANULADOS
    }
    # Límite superior del window: el ID numérico más alto retornado por AyC.
    # Solo se consideran locales con ID ≤ ese máximo para no tocar liquidaciones
    # más viejas que el top-N del SOAP (que podrían estar fuera del window).
    max_cd_id = max(cd_liq.id for cd_liq in liqs)

    anuladas = []
    for liq in locales:
        assert liq.numero_liquidacion is not None
        try:
            local_ayc_id = int(liq.numero_liquidacion.split("-")[0])
        except (ValueError, IndexError):
            continue
        if local_ayc_id <= max_cd_id and liq.numero_liquidacion not in cd_vigentes:
            anuladas.append(liq)
    return anuladas
