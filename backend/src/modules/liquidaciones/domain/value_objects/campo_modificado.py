"""Un campo que cambió entre lo que había localmente y lo que reporta AyC —
detalle que `_difiere()` (antes de esto) no conservaba, ver
`domain/services/campos_modificados_incidente.py`."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CampoModificado:
    campo: str
    valor_anterior: str
    valor_nuevo: str
