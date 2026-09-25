"""Orden de la tabla de preventivos. La tabla pagina en el servidor, así que
el orden por columna se resuelve acá, sobre el parque filtrado completo, y no
en el navegador sobre la página cargada.

Sin columna pedida rige el orden de negocio (`orden_default`); con columna,
ese mismo orden queda como desempate y los valores vacíos van al final en
ambos sentidos."""

from datetime import date, datetime

from src.modules.preventivos.application.dtos.equipo_preventivo_anotado import (
    EquipoPreventivoAnotado,
)
from src.modules.preventivos.application.dtos.list_equipos_request import CampoOrdenEquipos
from src.modules.preventivos.domain.services.vencimiento import ORDEN_ESTADO_PRIORIDAD

_Valor = str | int | date | datetime | None


def orden_default(anotado: EquipoPreventivoAnotado) -> tuple[int, int, str, str]:
    """Vencidos primero y el más atrasado arriba (la vista "se quedó sin
    servicios, qué le doy"); después los que nunca tuvieron preventivo, los
    por vencer más próximos, al día y sin frecuencia al final."""
    if anotado.estado == "vencido":
        secundario = -(anotado.dias_vencido or 0)
    elif anotado.proximo_vencimiento is not None:
        secundario = anotado.proximo_vencimiento.toordinal()
    else:
        secundario = 0
    cliente = anotado.equipo.cliente.lower()
    return (ORDEN_ESTADO_PRIORIDAD[anotado.estado], secundario, cliente, anotado.equipo.serie)


def _valor(anotado: EquipoPreventivoAnotado, campo: CampoOrdenEquipos) -> _Valor:
    """El valor que muestra cada columna (textos sin distinguir mayúsculas)."""
    equipo = anotado.equipo
    valores: dict[CampoOrdenEquipos, _Valor] = {
        "cliente": equipo.cliente.lower(),
        "sucursal": equipo.sucursal.lower(),
        "equipo": equipo.serie.lower(),
        "ultimo_preventivo": equipo.fecha_ultimo_preventivo,
        # 0 o NULL se muestran como "—".
        "frecuencia": equipo.frecuencia_dias or None,
        # Sin vencimiento real se muestra la fecha tentativa.
        "vencimiento": anotado.proximo_vencimiento or anotado.fecha_tentativa,
        "estado": ORDEN_ESTADO_PRIORIDAD[anotado.estado],
        "habilitado": anotado.habilitacion.habilitado_en if anotado.habilitacion else None,
    }
    return valores[campo]


def ordenar_equipos(
    anotados: list[EquipoPreventivoAnotado],
    campo: CampoOrdenEquipos | None,
    descendente: bool,
) -> list[EquipoPreventivoAnotado]:
    base = sorted(anotados, key=orden_default)
    if campo is None:
        return base
    con_valor = [a for a in base if _valor(a, campo) is not None]
    sin_valor = [a for a in base if _valor(a, campo) is None]
    # `sort` es estable también con reverse: los empates conservan el orden
    # default. Los valores de una misma columna son todos del mismo tipo (y
    # ninguno None acá), cosa que mypy no puede deducir de la unión.
    con_valor.sort(key=lambda a: _valor(a, campo), reverse=descendente)  # type: ignore[arg-type,return-value]
    return con_valor + sin_valor
