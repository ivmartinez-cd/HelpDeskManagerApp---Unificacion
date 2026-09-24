from datetime import date, timedelta

from src.modules.contadores.domain.value_objects.estimacion.receso_cliente import RecesoCliente


def recesos_aplicables(
    recesos: list[RecesoCliente], id_anexo: int, id_grupo_economico: int
) -> list[RecesoCliente]:
    """`Receso.AplicaA` del legacy: un receso con anexo aplica si coincide el
    anexo del proceso, sin mirar el grupo; uno sin anexo aplica si coincide
    el grupo económico del equipo."""
    return [r for r in recesos if _aplica(r, id_anexo, id_grupo_economico)]


def _aplica(receso: RecesoCliente, id_anexo: int, id_grupo_economico: int) -> bool:
    if receso.id_anexo is not None:
        return receso.id_anexo == id_anexo
    return receso.id_grupo_economico == id_grupo_economico


def dias_activos(desde: date, hasta: date, recesos: list[RecesoCliente]) -> int:
    """`DiasActivos(desde, hasta, recesos, 0)` del legacy: días calendario en
    (desde, hasta] menos los días de receso, contando una sola vez los días
    en que se superponen dos recesos. Nunca negativo."""
    total = (hasta - desde).days
    if total <= 0:
        return 0
    return max(total - len(_dias_de_receso(desde, hasta, recesos)), 0)


def dias_activos_par(desde: date, hasta: date, recesos: list[RecesoCliente]) -> int:
    """`DiasActivos(..., minimo: 1)`: el divisor de la tasa diaria nunca es 0
    aunque todo el tramo Partida→Llegada sea receso."""
    return max(dias_activos(desde, hasta, recesos), 1)


def dias_activos_proyeccion(
    llegada: date, fecha_objetivo: date, recesos: list[RecesoCliente]
) -> int:
    """`DiasActivosProyeccion` del legacy: con Llegada posterior a la fecha
    objetivo el resultado es negativo (interpolación hacia atrás) y también
    descuenta los recesos de ese tramo."""
    if fecha_objetivo >= llegada:
        return dias_activos(llegada, fecha_objetivo, recesos)
    return -dias_activos(fecha_objetivo, llegada, recesos)


def _dias_de_receso(desde: date, hasta: date, recesos: list[RecesoCliente]) -> set[date]:
    dias: set[date] = set()
    for receso in recesos:
        inicio = max(receso.fecha_desde, desde + timedelta(days=1))
        fin = min(receso.fecha_hasta, hasta)
        dias.update(inicio + timedelta(days=i) for i in range((fin - inicio).days + 1))
    return dias
