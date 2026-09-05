"""Adapter pyodbc del puerto CandidatosEquipoPort — panel de candidatos
manuales del Estimador contra Siges/MERCURIO. Plomería pyodbc en el
`MercurioQueryRunner` compartido (ADR-018), misma cuenta que el resto de
`contadores` (`SiGesReadOnly`, solo lectura)."""

from datetime import date, datetime
from typing import Any

from src.modules.contadores.domain.ports.candidatos_equipo_port import (
    LecturaCandidataSiges,
    MetadataEquipoSiges,
)
from src.modules.contadores.infrastructure.siges.candidatos_query import (
    CANDIDATOS_EQUIPO_SQL,
    METADATA_EQUIPO_SQL,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner

_GATEWAY = "candidatos_equipo"
_TIPO_TOMA_T4 = 4


class PyodbcCandidatosEquipoGateway:
    def __init__(self, runner: MercurioQueryRunner) -> None:
        self._runner = runner

    async def fetch_lecturas(
        self, id_maquina: int, id_clase_contador: int
    ) -> list[LecturaCandidataSiges]:
        rows = await self._runner.fetch_all(
            CANDIDATOS_EQUIPO_SQL,
            [id_maquina, id_clase_contador],
            gateway=_GATEWAY,
            log_message="Fallo la lista de candidatos del equipo contra Siges/MERCURIO",
            log_extra={"id_maquina": id_maquina, "id_clase_contador": id_clase_contador},
        )
        return [_lectura_de(r) for r in rows]

    async def fetch_metadata_equipo(self, id_maquina: int) -> MetadataEquipoSiges | None:
        rows = await self._runner.fetch_all(
            METADATA_EQUIPO_SQL,
            [id_maquina],
            gateway=_GATEWAY,
            log_message="Fallo la metadata del equipo contra Siges/MERCURIO",
            log_extra={"id_maquina": id_maquina},
        )
        if not rows:
            return None
        r = rows[0]
        return MetadataEquipoSiges(
            nro_serie=str(r.Nro_Serie),
            empresa=str(r.EmpresaDesc),
            sucursal=str(r.SucursalDesc),
            sector=r.SectorDesc,
            modelo=str(r.ModeloDesc),
            id_tecnologia=int(r.IdTecnologia),
            velocidad=float(r.Velocidad) if r.Velocidad is not None else None,
        )


def _lectura_de(r: Any) -> LecturaCandidataSiges:
    # T4 sin revisar: `Contadores.Para_Facturar` (a nivel de fila) en 0 — el
    # mismo criterio que ya usa la grilla real para "#T4ST" (ver docstring de
    # `candidatos_query.py`). Para el resto de los tipos de toma no aplica
    # ningún filtro de validez propio.
    es_t4_sin_revisar = int(r.ID_TipoToma) == _TIPO_TOMA_T4 and not r.Para_Facturar
    return LecturaCandidataSiges(
        fecha=_d(r.FechaTomaContador),
        tipo_toma=int(r.ID_TipoToma),
        valor=float(r.Contador),
        para_facturar=not es_t4_sin_revisar,
    )


def _d(valor: Any) -> date:
    """Mismo bug pyodbc/FreeTDS que en `pyodbc_grilla_estimacion_gateway.py`:
    una columna SQL `date` llega como `datetime.datetime`."""
    return valor.date() if isinstance(valor, datetime) else valor
