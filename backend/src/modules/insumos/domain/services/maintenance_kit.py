"""Detección de kits de mantenimiento — van como incidente Pre-Correctivo, no como
pedido de insumo. Port de is_maintenance_kit (canal_directo_incident_client.py)."""

_MAINTENANCE_KIT_REORDER_TYPES = frozenset({"MAINTENANCE_KIT"})

# Fallback por texto cuando reorderPart.type no está configurado para el SKU.
_MAINTENANCE_KIT_KEYWORDS = (
    "maintenance kit",
    "kit de mantenimiento",
    "maint kit",
    "fuser kit",
    "kit fusor",
    "pm kit",
    "roller kit",
    "imaging unit kit",
)


def is_maintenance_kit(description: str, reorder_part_type: str) -> bool:
    """Estrategia en orden de confianza: 1) reorderPart.type == 'MAINTENANCE_KIT'
    (campo estructurado de Insight, el más confiable); 2) keywords en la descripción.

    El `consumable.type` 'FUSER' NO se usa solo como criterio (el legacy lo recibía y
    lo ignoraba a propósito): algunos fusores simples no-kit también tienen ese tipo.
    """
    if reorder_part_type.upper() in _MAINTENANCE_KIT_REORDER_TYPES:
        return True
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in _MAINTENANCE_KIT_KEYWORDS)
