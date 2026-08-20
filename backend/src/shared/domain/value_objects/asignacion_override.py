import uuid
from dataclasses import dataclass
from datetime import date
from typing import Literal


@dataclass(slots=True, eq=False)
class AsignacionOverride[TOperadorId, TAlcanceId]:
    """Sustitución temporal de operador para uno o más elementos de alcance
    (vacaciones, licencia). Genérico sobre el tipo de id de operador
    (`str` en contadores -- username de Gestión --, `uuid.UUID` en
    prestadores/turnos) y el tipo de id de alcance (`str` = cliente en
    contadores, `uuid.UUID` = prestador/slot en prestadores/turnos). No toca
    la asignación real de cada módulo -- se resuelve en lectura (ver
    ADR-013). `hasta` es siempre obligatorio: a diferencia de una vigencia
    de asignación permanente, acá no existe vigencia abierta, por diseño.

    `intercambio_id` (ADR-026): dos overrides cruzados (A→B y B→A, mismo
    rango) forman un intercambio de turnos y comparten este id; `None` en
    una cobertura común. El resolver no lo mira -- solo agrupa para que el
    par se cree, edite y cancele junto. Hoy lo persiste `turnos`; los demás
    módulos lo ignoran."""

    id: uuid.UUID
    operador_ausente_id: TOperadorId
    operador_reemplazante_id: TOperadorId
    desde: date
    hasta: date
    alcance: Literal["TOTAL"] | frozenset[TAlcanceId]
    estado: Literal["ACTIVA", "CANCELADA"]
    motivo: str | None
    created_by_user_id: uuid.UUID
    intercambio_id: uuid.UUID | None = None

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AsignacionOverride) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
