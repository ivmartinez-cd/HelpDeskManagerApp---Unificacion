"""Diferencia campo a campo entre un incidente local y lo que reporta AyC.

Mismos campos y tolerancias que ya decidían si un incidente "cambió" en
`reconciliar_incidentes.py` (`_difiere`, antes de esto) — la diferencia es que acá
se conserva el detalle de qué campo cambió y con qué valores, para poder
registrar un `ModificacionPrestador` (antes se perdía: `_difiere` solo devolvía
un bool y `_a_actualizado` armaba directamente el estado final)."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.value_objects.campo_modificado import CampoModificado
from src.modules.liquidaciones.domain.value_objects.incidente_importado import IncidenteImportado

_TOLERANCIA_FLOAT = 0.005


def _str_difiere(local: Any, remoto: Any) -> bool:
    return (local or "") != remoto


def _float_difiere(local: Any, remoto: Any) -> bool:
    return abs(float(local) - float(remoto)) > _TOLERANCIA_FLOAT


def _bool_difiere(local: Any, remoto: Any) -> bool:
    return bool(local) != bool(remoto)


def _fmt_fecha(valor: Any) -> str:
    return valor.isoformat() if isinstance(valor, date) else "-"


def _fmt_bool(valor: Any) -> str:
    return "Sí" if valor else "No"


def _fmt_float(valor: Any) -> str:
    return f"{float(valor):.2f}"


@dataclass(frozen=True)
class _Campo:
    nombre: str
    local: Callable[[Incidente], Any]
    remoto: Callable[[IncidenteImportado], Any]
    difiere: Callable[[Any, Any], bool]
    formato: Callable[[Any], str]


_CAMPOS: tuple[_Campo, ...] = (
    _Campo("tipo", lambda i: i.tipo, lambda r: r.tipo, _str_difiere, str),
    _Campo(
        "empresa_nombre",
        lambda i: i.empresa_nombre,
        lambda r: r.empresa_nombre,
        _str_difiere,
        str,
    ),
    _Campo(
        "sucursal_nombre",
        lambda i: i.sucursal_nombre,
        lambda r: r.sucursal_nombre,
        _str_difiere,
        str,
    ),
    _Campo("nro_serie", lambda i: i.nro_serie, lambda r: r.nro_serie, _str_difiere, str),
    _Campo(
        "fecha_cierre",
        lambda i: i.fecha_cierre,
        lambda r: r.fecha_cierre,
        lambda local, remoto: local != remoto,
        _fmt_fecha,
    ),
    _Campo("pasa_it", lambda i: i.pasa_it, lambda r: r.pasa_it, _bool_difiere, _fmt_bool),
    _Campo(
        "costo_servicio_cobrado",
        lambda i: i.costo_servicio_cobrado,
        lambda r: r.costo_servicio_cobrado,
        _float_difiere,
        _fmt_float,
    ),
    _Campo(
        "cant_km_cobrado",
        lambda i: i.cant_km_cobrado,
        lambda r: r.cant_km_cobrado,
        _float_difiere,
        _fmt_float,
    ),
    _Campo(
        "costo_km_cobrado",
        lambda i: i.costo_km_cobrado,
        lambda r: r.costo_km_cobrado,
        _float_difiere,
        _fmt_float,
    ),
    _Campo(
        "total_viaje_cobrado",
        lambda i: i.total_viaje_cobrado,
        lambda r: r.total_viaje_cobrado,
        _float_difiere,
        _fmt_float,
    ),
    _Campo(
        "costo_total_cobrado",
        lambda i: i.costo_total_cobrado,
        lambda r: r.costo_total_cobrado,
        _float_difiere,
        _fmt_float,
    ),
)


def campos_modificados(local: Incidente, remoto: IncidenteImportado) -> list[CampoModificado]:
    return [
        CampoModificado(c.nombre, c.formato(c.local(local)), c.formato(c.remoto(remoto)))
        for c in _CAMPOS
        if c.difiere(c.local(local), c.remoto(remoto))
    ]
