from itertools import count

from src.modules.reporte_incidentes.domain.entities.incidente import Incidente

_seq = count(1)


def incidente(**campos: object) -> Incidente:
    """Incidente mínimo (mismo helper `inc()` de los tests del legacy)."""
    n = str(next(_seq))
    base: dict[str, object] = {
        "id": n, "numero": n, "fecha": "2026-06-01", "empresa_id": "1001",
        "empresa_nombre": "ACME", "descripcion": "caso",
    }
    return Incidente(**{**base, **campos})  # type: ignore[arg-type]
