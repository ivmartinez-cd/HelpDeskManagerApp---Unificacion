"""Diagnóstico automático de por qué una solicitud entró con un nivel sospechoso.

Port de validation_diagnosis.py del legacy. Junta, una sola vez por solicitud (al
arrancar la ventana de validación), la misma evidencia que se revisa a mano para
distinguir un glitch de sensor de una intervención real:

  - Cambio de cartucho: el chip físico (consumableSerial) cambió respecto a la última
    lectura conocida — caso real PHC5R18423 (ago-2026).
  - Glitch multicanal en curso: OTROS consumibles del mismo equipo también están casi
    en 0% ahora mismo — varios canales independientes no caen a la vez por consumo real.
  - Antecedente: este mismo consumible ya tuvo un episodio de caída y recuperación
    antes (caso real CN4766M07W, ago-2026).
  - ST técnico reciente: un incidente (Canal Directo, wsAyC) sobre este equipo, abierto
    o cerrado poco antes de la solicitud — caso real PHC5R18423 (ago-2026).

Cuando ninguna señal es concluyente se dice así explícitamente (no se adivina). Ninguna
de estas señales decide CONFIRMED/DISMISSED por sí sola: es evidencia para el operador;
la ventana de validación siempre espera el nivel EN VIVO antes de habilitar la carga.

Fechas de Insight: SIEMPRE a partir de `recordDate` (UTC verificado), convertidas a hora
Argentina con format_arg_datetime — `readDateLocal` NUNCA se usa acá (ver insight_datetime).
Fechas de Canal Directo: formato propio "DD/MM/YYYY HH:MM:SS", YA en hora Argentina
(parse_cd_datetime) — no hay conversión de huso que hacer.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway, JsonDict
from src.modules.insumos.domain.repositories.wsayc_gateway import WsAycGateway
from src.modules.insumos.domain.value_objects.cd_datetime import parse_cd_datetime
from src.modules.insumos.domain.value_objects.cd_supply import CdIncident
from src.modules.insumos.domain.value_objects.insight_datetime import format_arg_datetime

logger = logging.getLogger(__name__)

# Un consumible "casi en 0" para considerarlo parte de un glitch multicanal — no
# exactamente 0 porque distintos equipos redondean distinto (rawLevel vs percentLeft).
_LOW_THRESHOLD = 5

# Un ST cerrado más allá de esta ventana antes de la solicitud ya no es "reciente".
_INCIDENT_LOOKBACK_HOURS = 72

_NO_EVIDENCE = (
    "No se encontraron antecedentes ni caídas simultáneas en otros consumibles — "
    "podría ser una depleción real. Revisar el gráfico en el portal SDS antes de cargar."
)


@dataclass(frozen=True)
class Diagnosis:
    swap_note: str | None
    headline: str
    detail: str


class ValidationDiagnosis:
    """Best-effort: cualquier problema para consultar Insight simplemente no arma
    diagnóstico (None) — es una anotación informativa, no una decisión de negocio,
    así que nunca bloquea ni cuenta como fail-closed la ventana de validación."""

    def __init__(self, insight: InsightGateway, wsayc: WsAycGateway) -> None:
        self._insight = insight
        self._wsayc = wsayc

    async def build(
        self, device_id: int, request: JsonDict, device_serial: str = ""
    ) -> Diagnosis | None:
        consumable = request.get("consumable") or {}
        index = consumable.get("index")
        if index is None:
            return None
        own_history = await self._history(device_id, index, request.get("id"))
        if own_history is None:
            return None
        live = await self._live(device_id)
        swap_note = _swap_note(
            own_history, consumable.get("serialNumber"), consumable.get("percentLeft")
        )
        incident_note = await self._find_recent_incident(device_serial, request.get("requested"))
        return _compose(swap_note, incident_note, own_history, live, index)

    async def _history(
        self, device_id: int, index: int, request_id: object
    ) -> list[JsonDict] | None:
        try:
            return await self._insight.get_consumable_history(device_id, index)
        except Exception as exc:
            logger.error(
                "validation_diagnosis: no se pudo consultar el historial del equipo %s "
                "(solicitud %s) — sin diagnóstico automático",
                device_id,
                request_id,
                exc_info=exc,
            )
            return None

    async def _live(self, device_id: int) -> list[JsonDict]:
        try:
            return await self._insight.get_device_consumables(device_id)
        except Exception as exc:
            logger.warning(
                "validation_diagnosis: sin consumibles en vivo del equipo %s — se "
                "diagnostica sin el chequeo multicanal",
                device_id,
                exc_info=exc,
            )
            return []

    async def _find_recent_incident(
        self, device_serial: str, request_time_iso: object
    ) -> str | None:
        """Best-effort: si hubo un ST sobre este equipo cerca del momento de la
        solicitud, arma una nota — cualquier problema con CD simplemente no anota."""
        if not device_serial or not request_time_iso:
            return None
        try:
            machine = await self._wsayc.get_machine_by_serial(device_serial)
        except Exception as exc:
            logger.error(
                "validation_diagnosis: no se pudo consultar la máquina %s en Canal "
                "Directo — sin chequeo de ST técnico",
                device_serial,
                exc_info=exc,
            )
            return None
        if machine is None or not machine.machine_id:
            return None
        incidents = await self._wsayc.get_machine_incidents(machine.machine_id, top=3)
        request_dt = _parse_request_dt(str(request_time_iso))
        if request_dt is None:
            return None
        return next((n for i in incidents if (n := _incident_note(i, request_dt))), None)


def _mask(serial: object) -> str:
    s = str(serial or "")
    return f"…{s[-4:]}" if len(s) >= 4 else (s or "?")


def _swap_note(
    own_history: list[JsonDict], current_serial: str | None, current_percent: object
) -> str | None:
    if not current_serial or not own_history:
        return None
    latest = own_history[0]
    prev_serial = latest.get("consumableSerial")
    if not prev_serial or prev_serial == current_serial:
        return None  # mismo chip que la última lectura conocida: no hubo cambio físico
    return (
        f"Cambio de cartucho detectado: la última lectura conocida (chip "
        f"{_mask(prev_serial)}) estaba en {latest.get('level')}%, ahora hay un chip "
        f"distinto ({_mask(current_serial)}) reportando {current_percent}% — puede ser "
        "una reposición manual con un cartucho ya usado, no una falla de sensor."
    )


def _find_precedent(own_history: list[JsonDict]) -> tuple[str | None, str | None]:
    """Episodio de caída-y-recuperación más reciente en el historial del propio
    consumible (más reciente primero): una entrada baja seguida cronológicamente (el
    índice anterior en la lista) por una entrada alta."""
    for k in range(1, len(own_history)):
        low, high = own_history[k], own_history[k - 1]
        low_level, high_level = low.get("level"), high.get("level")
        if low_level is None or high_level is None:
            continue
        if low_level <= _LOW_THRESHOLD and high_level > _LOW_THRESHOLD:
            return _precedent_texts(low, high)
    return None, None


def _precedent_texts(low: JsonDict, high: JsonDict) -> tuple[str | None, str | None]:
    precedent = None
    if low.get("recordDate") and high.get("recordDate"):
        precedent = (
            f"Este mismo consumible ya cayó a {low.get('level')}% el "
            f"{format_arg_datetime(low['recordDate'])} y se recuperó solo a "
            f"{high.get('level')}% el {format_arg_datetime(high['recordDate'])} — sin "
            "que nadie interviniera."
        )
    engine_flat = None
    if low.get("engineCycles") is not None and low.get("engineCycles") == high.get("engineCycles"):
        engine_flat = (
            "En ese episodio el contador de ciclos de motor no cambió — no hubo "
            "impresión de por medio."
        )
    return precedent, engine_flat


def _format_cd_local(raw: str) -> str:
    """"DD/MM/YYYY HH:MM:SS" (CD, ya en hora Argentina) a "DD/MM HH:MM" — mismo formato
    de salida que format_arg_datetime, pero sin conversión de huso."""
    parsed = parse_cd_datetime(raw)
    return parsed.strftime("%d/%m %H:%M") if parsed is not None else raw.strip()


def _parse_request_dt(raw: str) -> datetime | None:
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _incident_note(incident: CdIncident, request_dt: datetime) -> str | None:
    if incident.estado == "Cerrado":
        close_raw = incident.fecha_cierre or incident.fecha
        close_dt = parse_cd_datetime(close_raw)
        if close_dt is None:
            return None
        hours_before = (request_dt - close_dt.astimezone(UTC)).total_seconds() / 3600
        if not (0 <= hours_before <= _INCIDENT_LOOKBACK_HOURS):
            return None  # cerrado hace demasiado (o después de la solicitud)
        fecha_txt = f"cerrado el {_format_cd_local(close_raw)}"
    else:
        fecha_txt = "todavía en curso"
    tecnico_txt = f", atendido por {incident.tecnico}" if incident.tecnico else ""
    motivo_txt = f" — motivo: {incident.motivo}" if incident.motivo else ""
    return (
        f"Hay un ST técnico (#{incident.numero or '?'}) {fecha_txt} en este equipo"
        f"{tecnico_txt}{motivo_txt} — una intervención humana reciente puede explicar "
        "el cambio de nivel."
    )


def _compose(
    swap_note: str | None,
    incident_note: str | None,
    own_history: list[JsonDict],
    live: list[JsonDict],
    index: int,
) -> Diagnosis:
    evidence, has_low_peers, precedent_text = _collect_evidence(
        own_history, live, index, incident_note
    )
    headline = _headline(swap_note, has_low_peers, incident_note, precedent_text)
    if headline is None:
        headline = "Sin antecedentes claros — validar manualmente"
        evidence.append(_NO_EVIDENCE)
    detail = "\n".join(f"• {e}" for e in evidence) if evidence else (
        "Sin evidencia adicional disponible."
    )
    return Diagnosis(swap_note=swap_note, headline=headline, detail=detail)


def _collect_evidence(
    own_history: list[JsonDict], live: list[JsonDict], index: int, incident_note: str | None
) -> tuple[list[str], bool, str | None]:
    evidence: list[str] = []
    if own_history and own_history[0].get("recordDate"):
        latest = own_history[0]
        evidence.append(
            f"Última lectura confiable de este consumible: {latest.get('level')}% "
            f"({format_arg_datetime(latest['recordDate'])})"
        )
    low_peers = _low_peers(live, index)
    if low_peers:
        names = ", ".join(
            f"{c.get('colour') or c.get('sku')} ({c['percentLeft']}%)" for c in low_peers
        )
        evidence.append(
            f"Otros consumibles del mismo equipo también están casi en 0% ahora mismo: {names}"
        )
    if incident_note:
        evidence.append(incident_note)
    precedent_text, engine_flat_text = _find_precedent(own_history)
    evidence.extend(text for text in (precedent_text, engine_flat_text) if text)
    return evidence, bool(low_peers), precedent_text


def _low_peers(live: list[JsonDict], index: int) -> list[JsonDict]:
    return [
        c
        for c in live
        if c.get("index") != index
        and isinstance(c.get("percentLeft"), int | float)
        and c["percentLeft"] <= _LOW_THRESHOLD
    ]


def _headline(
    swap_note: str | None,
    has_low_peers: bool,
    incident_note: str | None,
    precedent_text: str | None,
) -> str | None:
    if swap_note:
        return "Posible cambio de cartucho"
    if has_low_peers:
        return "Glitch de sensor (multicanal, en curso)"
    if incident_note:
        return "Intervención técnica reciente registrada"
    if precedent_text:
        return "Glitch de sensor (antecedente en este equipo)"
    return None
