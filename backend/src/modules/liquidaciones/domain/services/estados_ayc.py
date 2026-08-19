"""Mapa canónico de estados entre AyC y el dominio local de liquidaciones —
reemplaza los cuatro lugares que antes tenían esta info por separado y podían
desincronizarse entre sí: `_ESTADO_NOMBRE_A_ID` del gateway SOAP (escritura),
`_ESTADOS_AYC_VALIDOS` del backfill (lectura por nombre), las constantes
`ESTADO_*` del dominio, y los `_ESTADO_AYC` hardcodeados de aprobar/observar.

`estado_id` es el numérico que el propio SOAP espera para escribir
(`setLiquidationStatus`) — preferirlo sobre el nombre string cuando esté
disponible: pasar el nombre ("Aprobada") no aplica el cambio, pasar el id ("4")
sí (verificado 2026-08-14 con la liquidación 3929-7). El nombre normalizado a
minúsculas es el fallback para lectura cuando `estado_id` no vino en la
respuesta SOAP (`getTopLiquidations` sí lo trae; otras respuestas podrían no).

`abierta` es local-only — liquidaciones sin vínculo AyC (import CSV manual) o
recién creadas por el sync antes de la primera reconciliación. No tiene id ni
nombre AyC: `estado_id_para_escribir` nunca la recibe (el sync nunca escribe
"abierta" a AyC), `estado_local_desde_ayc` nunca la devuelve.
"""

from src.modules.liquidaciones.domain.entities.liquidacion import (
    ESTADO_APROBADA,
    ESTADO_CERRADA,
    ESTADO_OBSERVADA,
    ESTADO_PRELIQUIDADA,
    ESTADO_RECIBIDA,
)

_LOCAL_A_ID: dict[str, int] = {
    ESTADO_PRELIQUIDADA: 1,
    ESTADO_RECIBIDA: 2,
    ESTADO_OBSERVADA: 3,
    ESTADO_APROBADA: 4,
    ESTADO_CERRADA: 5,
}
_ID_A_LOCAL: dict[int, str] = {v: k for k, v in _LOCAL_A_ID.items()}


def estado_id_para_escribir(estado_local: str) -> int:
    """El id numérico que espera `setLiquidationStatus`. `KeyError` si
    `estado_local` es `abierta` u otro valor sin contraparte en AyC — nunca se
    escribe un estado así, es un error de uso del caller."""
    return _LOCAL_A_ID[estado_local]


def estado_local_desde_ayc(*, estado_id: int | None, nombre: str) -> str | None:
    """`estado_id` (preferido) o `nombre` (fallback, case-insensitive) a la
    constante local — `None` si ninguno matchea (estado AyC desconocido, ej.
    una variante de "Anulada" que ya maneja `_detectar_y_eliminar_anuladas`)."""
    if estado_id is not None and estado_id in _ID_A_LOCAL:
        return _ID_A_LOCAL[estado_id]
    candidato = nombre.strip().lower()
    return candidato if candidato in _LOCAL_A_ID else None
