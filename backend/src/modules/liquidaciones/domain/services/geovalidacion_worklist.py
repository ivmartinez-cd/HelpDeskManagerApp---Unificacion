"""Worklist final de geovalidación (Fase 2, cierre): cruza Tier 0 + Tier 1b
para calcular qué sucursales siguen con evidencia de un problema DESPUÉS de
los tiers gratis — ese es el único residuo que amerita gastar Google (Tier
2), principio central del plan ("a Google solo llega el residuo"). Dominio
puro: recibe hallazgos ya calculados, no hace I/O."""

from dataclasses import dataclass

# Certeza absoluta: geométricamente ya se sabe que el pin está mal (fuera del
# país, o lat/lon invertidas) — no necesitan ninguna verificación adicional,
# van directo a "corregir en Gestión", nunca a Tier 2.
_CODIGOS_CERTEZA_ABSOLUTA = frozenset({"fuera_de_argentina", "latlon_invertidas"})

# sin_coordenadas no es candidato a Tier 2 (Auditar Pines): sin pin no hay
# nada que comparar contra el geocode — esas van por el flujo ya existente
# de geocodificar-faltantes (llena vacíos, no compara).
_CODIGOS_EXCLUIDOS_DE_TIER2 = _CODIGOS_CERTEZA_ABSOLUTA | frozenset({"sin_coordenadas"})


@dataclass(frozen=True)
class ResiduoTier2:
    certeza_absoluta: frozenset[int]
    requiere_verificacion: frozenset[int]


def calcular_residuo(
    hallazgos_tier0: list[tuple[int, str]], confirmados_tier1b: set[int]
) -> ResiduoTier2:
    """`hallazgos_tier0`: (siges_sucursal_id, codigo) de cada hallazgo Tier 0.
    `confirmados_tier1b`: ids ya confirmados por dos fuentes independientes
    (Georef + Nominatim de acuerdo) — esos ya tienen evidencia suficiente,
    no hace falta gastar Google en ellos tampoco."""
    certeza = {sid for sid, codigo in hallazgos_tier0 if codigo in _CODIGOS_CERTEZA_ABSOLUTA}
    candidatos = {
        sid for sid, codigo in hallazgos_tier0 if codigo not in _CODIGOS_EXCLUIDOS_DE_TIER2
    }
    return ResiduoTier2(
        certeza_absoluta=frozenset(certeza),
        requiere_verificacion=frozenset(candidatos - confirmados_tier1b - certeza),
    )
