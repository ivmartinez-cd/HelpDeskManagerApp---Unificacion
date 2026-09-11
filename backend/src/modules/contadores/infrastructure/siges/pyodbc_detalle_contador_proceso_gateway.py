"""Adapter pyodbc del puerto DetalleContadorProcesoPort — reporte completo
"Detalle de contadores por nro de proceso" (reporte, no herramienta de
export: a diferencia de `PyodbcFaltaContadorProcesoGateway`, este gateway
alimenta una pantalla de solo lectura).

Una sola consulta (a diferencia del gateway de falta contador, que consulta
cliente y filas por separado): acá cada fila ya trae su propia `empresa`
(snapshot de `Factura_Contador`), así que un resultado vacío ES la señal de
"proceso no encontrado" (ver docstring de `DetalleContadorProcesoPort`).

Sin caché TTL, mismo motivo que el gateway de falta contador: cada consulta
lleva un `Nro_Proceso` distinto por invocación."""

from typing import Any

from src.modules.contadores.domain.errors import ProcesoNoEncontradoError
from src.modules.contadores.domain.ports.detalle_contador_proceso_port import (
    DetalleContadorProceso,
)
from src.modules.contadores.domain.value_objects.detalle_contador_row import (
    DetalleContadorRow,
)
from src.modules.contadores.infrastructure.siges.detalle_contador_proceso_query import (
    DETALLE_CONTADORES_POR_PROCESO_SQL,
)
from src.shared.infrastructure.orion.query_runner import OrionQueryRunner

_CLASE_NOMBRE = {10: "Mono", 20: "Color"}


class PyodbcDetalleContadorProcesoGateway:
    def __init__(self, runner: OrionQueryRunner) -> None:
        self._runner = runner

    async def fetch(self, nro_proceso: int) -> DetalleContadorProceso:
        rows = await self._runner.fetch_all(
            DETALLE_CONTADORES_POR_PROCESO_SQL,
            (nro_proceso,),
            gateway="detalle_contador_proceso",
            log_message=(
                "Fallo la consulta de detalle de contadores por proceso contra Siges/ORION"
            ),
        )
        if not rows:
            raise ProcesoNoEncontradoError(nro_proceso)

        filas = [_to_row(r) for r in rows]
        return DetalleContadorProceso(cliente=filas[0].empresa, filas=filas)


def _to_row(row: Any) -> DetalleContadorRow:
    falta_contador = bool(row.falta_contador)
    nombre_clase = _CLASE_NOMBRE.get(row.clase)
    return DetalleContadorRow(
        empresa=row.empresa.strip(),
        sucursal=row.sucursal.strip(),
        sector=row.sector.strip() if row.sector else None,
        modelo=row.modelo.strip(),
        serie=row.serie.strip(),
        nombre_clase=nombre_clase,
        estado_maquina=row.estado_maquina.strip() if row.estado_maquina else None,
        direccion_ip=(row.direccion_ip or "").strip() or None,
        mascara_ip=(row.mascara_ip or "").strip() or None,
        falta_contador=falta_contador,
        tipo=_tipo(falta_contador, bool(row.es_automatico), nombre_clase),
        **_lecturas(row, falta_contador),
    )


def _lecturas(row: Any, falta_contador: bool) -> dict[str, Any]:
    return {
        "fecha_toma_anterior": (
            row.fecha_toma_anterior.date() if row.fecha_toma_anterior else None
        ),
        "contador_anterior": row.contador_anterior,
        "fecha_toma_actual": row.fecha_toma_actual.date() if row.fecha_toma_actual else None,
        # "Contador Act." del reporte NO repite el valor viejo en una fila
        # "Falta Contador" (mismo registro físico para actual y anterior) —
        # verificado contra la captura real, ver docstring de la query.
        "contador_actual": 0 if falta_contador else row.contador_actual_bruto,
        "impresiones_reales": float(row.impresiones_reales),
    }


def _tipo(falta_contador: bool, es_automatico: bool, nombre_clase: str | None) -> str | None:
    if falta_contador:
        return f"FALTA CONTADOR {nombre_clase}" if nombre_clase else "FALTA CONTADOR"
    if es_automatico:
        return "AUTOMATICO"
    # Lectura real con delta != 0: el reporte legacy no está investigado
    # para este caso — no se inventa una etiqueta.
    return None
