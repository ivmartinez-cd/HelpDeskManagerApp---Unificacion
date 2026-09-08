"""Adapter pyodbc del puerto HistorialEquipoPort — línea de tiempo de un
equipo contra Siges/MERCURIO. Plomería pyodbc en el `MercurioQueryRunner`
compartido (ADR-018), misma cuenta que el resto de `contadores`
(`SiGesReadOnly`, solo lectura)."""

from datetime import date, datetime
from typing import Any

from src.modules.contadores.domain.ports.historial_equipo_port import LecturaHistorialSiges
from src.modules.contadores.infrastructure.siges.historial_equipo_query import (
    HISTORIAL_EQUIPO_SQL,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner

_GATEWAY = "historial_equipo"


class PyodbcHistorialEquipoGateway:
    def __init__(self, runner: MercurioQueryRunner) -> None:
        self._runner = runner

    async def fetch_historial(
        self, id_maquina: int, id_clase_contador: int, desde: date
    ) -> list[LecturaHistorialSiges]:
        base = [id_maquina, id_clase_contador]
        params = [*base, *base, desde, *base, desde]
        rows = await self._runner.fetch_all(
            HISTORIAL_EQUIPO_SQL,
            params,
            gateway=_GATEWAY,
            log_message="Fallo el historial del equipo contra Siges/MERCURIO",
            log_extra={"id_maquina": id_maquina, "id_clase_contador": id_clase_contador},
        )
        return [_lectura_de(r) for r in rows]


def _lectura_de(r: Any) -> LecturaHistorialSiges:
    return LecturaHistorialSiges(
        fecha=_d(r.Fecha),
        valor=float(r.Valor),
        id_tipo_toma=int(r.ID_TipoToma),
        tipo_toma_desc=str(r.TipoTomDesc),
        para_facturar=bool(r.Para_Facturar),
        fc_nro_proceso=int(r.FC_NroProceso) if r.FC_NroProceso is not None else None,
        fc_periodo_hasta=_d(r.FC_PeriodoHasta) if r.FC_PeriodoHasta is not None else None,
        fc_impresiones=float(r.FC_Impresiones) if r.FC_Impresiones is not None else None,
        fc_periodo_facturacion=r.FC_PeriodoFact,
        id_factura=int(r.ID_Factura),
        snap_id_empresa=int(r.Snap_ID_Empresa) if r.Snap_ID_Empresa is not None else None,
        snap_id_sucursal=int(r.Snap_ID_Sucursal) if r.Snap_ID_Sucursal is not None else None,
        snap_id_anexo=int(r.Snap_ID_Anexo) if r.Snap_ID_Anexo is not None else None,
    )


def _d(valor: Any) -> date:
    """Mismo bug pyodbc/FreeTDS que en `pyodbc_grilla_estimacion_gateway.py`:
    una columna SQL `date` llega como `datetime.datetime`."""
    return valor.date() if isinstance(valor, datetime) else valor
