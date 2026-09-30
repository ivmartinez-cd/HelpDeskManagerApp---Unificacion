"""Mail de aviso: casos de Mesa de Ayuda con una visita de técnico en marcha en
la misma sucursal. Un solo mail por ciclo con todos los pares nuevos, a los
destinatarios de `MESA_AYUDA_ALERTA_MAIL_TO`. Si el envío falla, lanza — el
caso de uso no registra los pares y el próximo ciclo reintenta."""

from html import escape

from src.modules.auth.domain.services.mailer import Mailer
from src.modules.sla.domain.entities.incidente_mesa_ayuda import IncidenteMesaAyuda

_ASUNTO = "Mesa de Ayuda: {n} caso(s) con visita de técnico en la misma sucursal"
_COLUMNAS = ("Caso MDA", "Cliente", "Sucursal", "Visita", "Técnico", "Estado visita")


def _celdas(inc: IncidenteMesaAyuda) -> tuple[str, ...]:
    extra = inc.visitas_en_sucursal - 1
    visita = f"{inc.visita_id_incidente}" + (f" (+{extra} más)" if extra > 0 else "")
    return (
        str(inc.id_incidente),
        inc.cliente,
        inc.sucursal,
        visita,
        inc.visita_tecnico or "",
        inc.visita_estado or "",
    )


def _texto(incidentes: list[IncidenteMesaAyuda]) -> str:
    lineas = [" | ".join(_celdas(i)) for i in incidentes]
    return (
        "Estos casos de Mesa de Ayuda tienen otro caso de la misma sucursal ya "
        "derivado a un técnico. Coordinar para que la visita cubra los dos.\n\n"
        + " | ".join(_COLUMNAS)
        + "\n"
        + "\n".join(lineas)
    )


def _html(incidentes: list[IncidenteMesaAyuda]) -> str:
    th = "".join(f"<th align='left'>{escape(c)}</th>" for c in _COLUMNAS)
    filas = "".join(
        "<tr>" + "".join(f"<td>{escape(c)}</td>" for c in _celdas(i)) + "</tr>"
        for i in incidentes
    )
    return (
        "<p>Estos casos de Mesa de Ayuda tienen otro caso de la misma sucursal ya "
        "derivado a un técnico. Coordinar para que la visita cubra los dos.</p>"
        f"<table cellpadding='4' border='1' style='border-collapse:collapse'>"
        f"<tr>{th}</tr>{filas}</table>"
    )


class EmailNotificadorVisitaSucursal:
    def __init__(self, mailer: Mailer, destinatarios: list[str]) -> None:
        self._mailer = mailer
        self._destinatarios = destinatarios

    async def avisar(self, incidentes: list[IncidenteMesaAyuda]) -> None:
        # Un solo envío con todos en To: o llega a todos o a nadie, y el
        # reintento del próximo ciclo no duplica a los que ya lo recibieron.
        await self._mailer.send(
            to=", ".join(self._destinatarios),
            subject=_ASUNTO.format(n=len(incidentes)),
            body=_texto(incidentes),
            html_body=_html(incidentes),
        )
