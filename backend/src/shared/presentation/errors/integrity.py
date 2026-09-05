"""Traducción central de `IntegrityError` (Postgres, clase SQLSTATE 23) a la
envelope de error de la app (ARCHITECTURE_GUIDE.md §6).

Es la red de seguridad, no el camino feliz: cada caso de uso debería validar
duplicados y referencias antes de escribir. Pero una violación de unicidad o
de clave foránea que llegue hasta acá significa "conflicto" o "referencia
inexistente", nunca un error interno — hasta el 2026-09-05 terminaban en 500
en auth (permisos/funciones), turnos, prestadores y liquidaciones.
"""

import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

_UNIQUE_VIOLATION = "23505"
_FOREIGN_KEY_VIOLATION = "23503"
_NOT_NULL_VIOLATION = "23502"
_CHECK_VIOLATION = "23514"


def _causas(exc: IntegrityError) -> tuple[object, ...]:
    # El adapter asyncpg de SQLAlchemy copia `sqlstate` al `orig` y encadena
    # la excepción real de asyncpg (que trae `constraint_name`) como `__cause__`.
    orig = exc.orig
    return (orig, getattr(orig, "__cause__", None))


def _sqlstate(exc: IntegrityError) -> str | None:
    for causa in _causas(exc):
        code = getattr(causa, "sqlstate", None) or getattr(causa, "pgcode", None)
        if code:
            return str(code)
    return None


def _constraint(exc: IntegrityError) -> str | None:
    for causa in _causas(exc):
        nombre = getattr(causa, "constraint_name", None)
        if nombre:
            return str(nombre)
    return None


def _es_borrado_referenciado(exc: IntegrityError) -> bool:
    return "update or delete on table" in str(exc.orig)


_Traduccion = tuple[int, str, str]
_RESTRICCION = (
    status.HTTP_400_BAD_REQUEST,
    "VALIDATION_ERROR",
    "Los datos no cumplen las restricciones del registro.",
)
_POR_SQLSTATE: dict[str | None, _Traduccion] = {
    _UNIQUE_VIOLATION: (
        status.HTTP_409_CONFLICT,
        "CONFLICTO_DUPLICADO",
        "Ya existe un registro con esos datos.",
    ),
    _NOT_NULL_VIOLATION: _RESTRICCION,
    _CHECK_VIOLATION: _RESTRICCION,
}
_FK_EN_INSERT: _Traduccion = (
    status.HTTP_404_NOT_FOUND,
    "REFERENCIA_INEXISTENTE",
    "Alguno de los registros referenciados no existe.",
)
_FK_EN_DELETE: _Traduccion = (
    status.HTTP_409_CONFLICT,
    "EN_USO",
    "El registro está referenciado por otros y no se puede borrar.",
)
_DESCONOCIDO: _Traduccion = (
    status.HTTP_500_INTERNAL_SERVER_ERROR,
    "INTERNAL_ERROR",
    "Error interno del servidor.",
)


def traducir_integrity_error(exc: IntegrityError) -> _Traduccion:
    """(http_status, code, message). Un SQLSTATE desconocido sigue siendo 500."""
    state = _sqlstate(exc)
    if state == _FOREIGN_KEY_VIOLATION:
        return _FK_EN_DELETE if _es_borrado_referenciado(exc) else _FK_EN_INSERT
    return _POR_SQLSTATE.get(state, _DESCONOCIDO)


async def handle_integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
    http_status, code, message = traducir_integrity_error(exc)
    constraint = _constraint(exc)
    extra = {
        "request_id": getattr(request.state, "request_id", None),
        "code": code,
        "sqlstate": _sqlstate(exc),
        "constraint": constraint,
    }
    if http_status == status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.exception("IntegrityError no traducido", extra=extra)
    else:
        logger.warning("IntegrityError traducido a %s", http_status, extra=extra)
    details = {"constraint": constraint} if constraint else None
    content = {"message": message, "code": code, "details": details}
    return JSONResponse(status_code=http_status, content=content)
