"""Templates de los emails de vacaciones — port de `utils/email.ts` del legacy
(mismo layout HTML, mismos subjects, fechas dd/mm/aa de `formatDateAR`), más la
versión texto plano que el mailer usa como fallback multipart."""

from dataclasses import dataclass
from datetime import date
from html import escape

from src.modules.vacaciones.domain.repositories.notificador import (
    DecisionNotif,
    NuevaSolicitudNotif,
)


@dataclass(frozen=True, slots=True)
class EmailContent:
    subject: str
    text: str
    html: str


def _fecha_ar(d: date) -> str:
    """`formatDateAR` legacy: dd/mm/aa."""
    return f"{d.day:02d}/{d.month:02d}/{d.year % 100:02d}"


def email_decision(notif: DecisionNotif) -> EmailContent:
    estado = "APROBADA" if notif.aprobada else "RECHAZADA"
    color = "#10b981" if notif.aprobada else "#ef4444"
    inicio, fin = _fecha_ar(notif.start_date), _fecha_ar(notif.end_date)
    comentario_html = (
        f"<p><em>Comentario del administrador:</em> {escape(notif.comment)}</p>"
        if notif.comment
        else ""
    )
    comentario_texto = (
        f"Comentario del administrador: {notif.comment}\n" if notif.comment else ""
    )
    html = f"""
  <div style="font-family:Inter,Arial,sans-serif;max-width:560px;margin:auto">
    <h2 style="color:{color}">Tu solicitud de vacaciones ha sido {estado}</h2>
    <p>Hola {escape(notif.empleado_nombre)},</p>
    <p>Tu solicitud de vacaciones del <strong>{inicio}</strong> al <strong>{fin}</strong>
       ha sido <strong style="color:{color}">{estado.lower()}</strong>.</p>
    {comentario_html}
    <hr style="border:none;border-top:1px solid #e5e7eb"/>
    <p style="color:#6b7280;font-size:12px">Canal Directo — Vacaciones</p>
  </div>"""
    text = (
        f"Hola {notif.empleado_nombre},\n\n"
        f"Tu solicitud de vacaciones del {inicio} al {fin} ha sido {estado.lower()}.\n"
        f"{comentario_texto}\n"
        "Canal Directo — Vacaciones"
    )
    return EmailContent(
        subject=f"Solicitud de vacaciones {estado} — Canal Directo", text=text, html=html
    )


_ESTILO_BOTON = (
    "background-color:#2563eb;color:#ffffff;padding:10px 18px;text-decoration:none;"
    "border-radius:6px;font-weight:500;display:inline-block"
)


def email_nueva_solicitud(notif: NuevaSolicitudNotif, frontend_url: str) -> EmailContent:
    inicio, fin = _fecha_ar(notif.start_date), _fecha_ar(notif.end_date)
    link = f"{frontend_url.rstrip('/')}/vacaciones/aprobaciones"
    html = f"""
  <div style="font-family:Inter,Arial,sans-serif;max-width:560px;margin:auto">
    <h2 style="color:#2563eb">Nueva solicitud de vacaciones recibida</h2>
    <p>Hola,</p>
    <p>El empleado <strong>{escape(notif.empleado_nombre)}</strong> del sector
       <strong>{escape(notif.sector_nombre)}</strong> ha registrado una nueva
       solicitud de vacaciones.</p>
    <table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:14px">
      {_fila_html("Desde:", inicio)}
      {_fila_html("Hasta:", fin)}
      {_fila_html("Días solicitados:", str(notif.dias))}
      {_fila_html("Año correspondiente:", str(notif.target_year))}
      {_fila_html("Motivo:", escape(notif.reason), italica=True) if notif.reason else ""}
    </table>
    <div style="margin:24px 0">
      <a href="{link}" style="{_ESTILO_BOTON}">Revisar solicitud en el sistema</a>
    </div>
    <hr style="border:none;border-top:1px solid #e5e7eb"/>
    <p style="color:#6b7280;font-size:12px">Canal Directo — Vacaciones</p>
  </div>"""
    motivo_texto = f"Motivo: {notif.reason}\n" if notif.reason else ""
    text = (
        f"El empleado {notif.empleado_nombre} del sector {notif.sector_nombre} "
        "ha registrado una nueva solicitud de vacaciones.\n\n"
        f"Desde: {inicio}\nHasta: {fin}\nDías solicitados: {notif.dias}\n"
        f"Año correspondiente: {notif.target_year}\n{motivo_texto}\n"
        f"Revisar solicitud en el sistema: {link}\n\n"
        "Canal Directo — Vacaciones"
    )
    return EmailContent(
        subject=f"Nueva solicitud de vacaciones — {notif.empleado_nombre} — Canal Directo",
        text=text,
        html=html,
    )


def _fila_html(label: str, valor: str, *, italica: bool = False) -> str:
    estilo_valor = "font-style:italic" if italica else "font-weight:600"
    return (
        "<tr>"
        f'<td style="padding:8px 0;color:#6b7280;width:150px;vertical-align:top">{label}</td>'
        f'<td style="padding:8px 0;{estilo_valor}">{valor}</td>'
        "</tr>"
    )
