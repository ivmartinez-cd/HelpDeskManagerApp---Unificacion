from datetime import date, timedelta

from src.modules.contadores.domain.value_objects.estimacion.receso_cliente import RecesoCliente


def recesos_aplicables(
    recesos: list[RecesoCliente], id_anexo: int, id_grupo_economico: int
) -> list[RecesoCliente]:
    """Filtra por alcance (REGLAS_DE_NEGOCIO §6): un receso por anexo
    específico solo aplica a ese anexo; uno definido solo por grupo
    económico (sin anexo) aplica a cualquier anexo de ese grupo."""
    return [
        r
        for r in recesos
        if r.id_grupo_economico == id_grupo_economico
        and (r.id_anexo is None or r.id_anexo == id_anexo)
    ]


def dias_activos(desde: date, hasta: date, recesos: list[RecesoCliente]) -> int:
    """Días calendario entre `desde` y `hasta`, descontando los días de
    receso que caen en ese tramo — "un día de receso equivale a cero
    impresiones" (REGLAS_DE_NEGOCIO §6). Si `hasta` es anterior a `desde`
    (interpolación hacia atrás, §5.2), se devuelve el total negativo sin
    descuento: no hay un tramo hacia adelante bien definido para recesar."""
    total = (hasta - desde).days
    if total <= 0:
        return total
    return max(total - dias_receso_en_tramo(desde, hasta, recesos), 0)


def dias_receso_en_tramo(desde: date, hasta: date, recesos: list[RecesoCliente]) -> int:
    """Días de receso descontados en (desde, hasta] — expuesto aparte de
    `dias_activos` para la auditoría (§11: "cuántos días se descontaron")."""
    if hasta <= desde:
        return 0
    return sum(_dias_receso_en_tramo(r, desde, hasta) for r in recesos)


def _dias_receso_en_tramo(receso: RecesoCliente, desde: date, hasta: date) -> int:
    ini = max(receso.fecha_desde, desde + timedelta(days=1))
    fin = min(receso.fecha_hasta, hasta)
    if ini > fin:
        return 0
    return (fin - ini).days + 1
