"""Adapter pyodbc del puerto FaltaContadorProcesoPort — consulta en vivo a
Siges para Estimación en 0 (ver `falta_contador_proceso_query.py`).

Sin caché TTL, a diferencia de los demás gateways de contadores: acá cada
consulta lleva un parámetro (`Nro_Proceso`) distinto por invocación — no hay
"mismo universo, otra pasada de la UI" que valga la pena cachear."""

from typing import Any

from src.modules.contadores.domain.errors import ProcesoNoEncontradoError
from src.modules.contadores.domain.ports.falta_contador_proceso_port import (
    ProcesoFaltaContador,
)
from src.modules.contadores.domain.value_objects.falta_contador_source_row import (
    FaltaContadorSourceRow,
)
from src.modules.contadores.infrastructure.siges.falta_contador_proceso_query import (
    CLIENTE_POR_PROCESO_SQL,
    FALTA_CONTADOR_POR_PROCESO_SQL,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner

_CLASE_NOMBRE = {10: "Mono", 20: "Color"}
_TIPO_FALTA_CONTADOR = "FALTA CONTADOR"


class PyodbcFaltaContadorProcesoGateway:
    def __init__(self, runner: MercurioQueryRunner) -> None:
        self._runner = runner

    async def fetch(self, nro_proceso: int) -> ProcesoFaltaContador:
        cliente_rows = await self._runner.fetch_all(
            CLIENTE_POR_PROCESO_SQL,
            (nro_proceso,),
            gateway="falta_contador_proceso_cliente",
            log_message="Fallo la consulta de cliente por proceso contra Siges/MERCURIO",
        )
        if not cliente_rows:
            raise ProcesoNoEncontradoError(nro_proceso)

        rows = await self._runner.fetch_all(
            FALTA_CONTADOR_POR_PROCESO_SQL,
            (nro_proceso,),
            gateway="falta_contador_proceso",
            log_message="Fallo la consulta de falta contador por proceso contra Siges/MERCURIO",
        )
        return ProcesoFaltaContador(
            cliente=cliente_rows[0].cliente.strip(),
            filas=[_to_source_row(r) for r in rows],
        )


def _to_source_row(row: Any) -> FaltaContadorSourceRow:
    return FaltaContadorSourceRow(
        tipo=_TIPO_FALTA_CONTADOR,
        serie=row.serie.strip(),
        contador=row.contador,
        nombre_clase=_CLASE_NOMBRE.get(row.clase),
    )
