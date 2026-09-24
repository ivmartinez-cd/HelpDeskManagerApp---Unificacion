"""Adapter pyodbc del puerto CandidatosEquipoPort — panel de candidatos
manuales del Estimador contra Siges/ORION. Plomería pyodbc en el
`OrionQueryRunner` compartido (ADR-018), misma cuenta que el resto de
`contadores` (`SiGesReadOnly`, solo lectura). El mapeo y las marcas de cambio
de ubicación replican `SiGesRepository.GetCandidatosAsync` del legacy."""

from dataclasses import replace
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
from src.shared.infrastructure.orion.query_runner import OrionQueryRunner

_GATEWAY = "candidatos_equipo"


class PyodbcCandidatosEquipoGateway:
    def __init__(self, runner: OrionQueryRunner) -> None:
        self._runner = runner

    async def fetch_lecturas(
        self, id_maquina: int, id_clase_contador: int
    ) -> list[LecturaCandidataSiges]:
        rows = await self._runner.fetch_all(
            CANDIDATOS_EQUIPO_SQL,
            [id_maquina, id_clase_contador],
            gateway=_GATEWAY,
            log_message="Fallo la lista de candidatos del equipo contra Siges/ORION",
            log_extra={"id_maquina": id_maquina, "id_clase_contador": id_clase_contador},
        )
        return marcar_cambios_de_ubicacion([_lectura_de(r) for r in rows])

    async def fetch_metadata_equipo(self, id_maquina: int) -> MetadataEquipoSiges | None:
        rows = await self._runner.fetch_all(
            METADATA_EQUIPO_SQL,
            [id_maquina],
            gateway=_GATEWAY,
            log_message="Fallo la metadata del equipo contra Siges/ORION",
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
            velocidad=float(round(r.Velocidad)) if r.Velocidad is not None else None,
        )


def _lectura_de(r: Any) -> LecturaCandidataSiges:
    """Lectura posicional, mismo orden de columnas que `GetCandidatos.sql`
    (0 ID_Contador … 10 ID_Anexo). Las columnas 1-2 (máquina y clase) son
    los parámetros de la consulta: no se vuelven a guardar."""
    return LecturaCandidataSiges(
        id_contador=int(r[0]),
        fecha=_d(r[3]),
        valor=float(r[4]),
        tipo_toma=int(r[5]),
        desc_tipo_toma=str(r[6]) if r[6] is not None else "",
        para_facturar=bool(r[7]),
        id_empresa=_i(r[8]),
        id_sucursal=_i(r[9]),
        id_anexo=_i(r[10]),
    )


def marcar_cambios_de_ubicacion(
    lecturas: list[LecturaCandidataSiges],
) -> list[LecturaCandidataSiges]:
    """Cada lectura contra la siguiente de la lista (más vieja): cambio de
    empresa, si no de sucursal, si no de anexo — solo cuando ambos snapshots
    tienen dato. La última lectura nunca se marca (no hay contra qué)."""
    marcadas = [_con_cambio(a, b) for a, b in zip(lecturas, lecturas[1:], strict=False)]
    return marcadas + lecturas[-1:]


def _con_cambio(
    actual: LecturaCandidataSiges, anterior: LecturaCandidataSiges
) -> LecturaCandidataSiges:
    empresa = _distinto(actual.id_empresa, anterior.id_empresa)
    sucursal = not empresa and _distinto(actual.id_sucursal, anterior.id_sucursal)
    anexo = not empresa and not sucursal and _distinto(actual.id_anexo, anterior.id_anexo)
    if not (empresa or sucursal or anexo):
        return actual
    return replace(
        actual,
        cambio_empresa_vs_anterior=empresa,
        cambio_sucursal_vs_anterior=sucursal,
        cambio_anexo_vs_anterior=anexo,
    )


def _distinto(a: int | None, b: int | None) -> bool:
    return a is not None and b is not None and a != b


def _i(valor: Any) -> int | None:
    return int(valor) if valor is not None else None


def _d(valor: Any) -> date:
    """Mismo bug pyodbc/FreeTDS que en `pyodbc_grilla_estimacion_gateway.py`:
    una columna SQL `date` llega como `datetime.datetime`."""
    return valor.date() if isinstance(valor, datetime) else valor
