from typing import Protocol

from src.modules.bono_tecnicos.domain.entities.conteo_tecnico import ConteoTecnico
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


class ConteoTecnicoGateway(Protocol):
    """Puerto de consulta en vivo a la base Siges (servidor MERCURIO). La
    implementación agrupa por técnico y categoría con Desde/Hasta derivados
    del período (primer/último día del mes) y devuelve un `ConteoTecnico` por
    cada técnico de planta ("CD - ...") con al menos un incidente en el período."""

    async def find_conteos(self, periodo: Periodo) -> list[ConteoTecnico]: ...

    async def find_conteos_anio(self, anio: int) -> list[ConteoTecnico]:
        """Los mismos conteos que `find_conteos`, pero de los 12 meses del
        año en una sola consulta (una fila por técnico+mes con actividad) —
        evita 12 llamadas al semáforo compartido de MERCURIO (ADR-018).
        Cacheado por implementación: los meses cerrados no cambian."""
        ...
