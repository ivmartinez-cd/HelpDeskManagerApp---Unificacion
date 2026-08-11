"""Ventana de validación para solicitudes con nivel sospechoso — port de
request_validation.py del legacy.

Caso real que motivó esto (equipo MXBCQ7C03T, ago-2026): un glitch de lectura del
sensor hizo que Insight reportara un cartucho al 0% cuando seguía en ~87% — la
solicitud se generó igual, la app la autocargó 23 minutos después, y para entonces
Insight ya tenía el nivel real hacía más de dos horas. El problema no era de timing:
nadie volvía a consultar el dato fresco antes de actuar.

De las solicitudes elegibles para autocarga (is_autoload_eligible), solo las que
llegan en 0% (needs_validation) entran acá la primera vez que se ven — hoy vía
list_requests; cuando llegue el poller, también por la autocarga (ambos llaman
start_pending, idempotente). Mientras esté PENDING, ni la autocarga ni el botón
"Cargar" actúan — el diagnóstico automático es puramente informativo, nunca decide:
lo único que saca a una solicitud de PENDING es volver a consultar el nivel EN VIVO.

DISMISSED también da de baja la solicitud en HP SDS (mismo status_update=DELETE que
el "Descartar" manual) con el detalle como comentario. Es best-effort: si la baja en
Insight falla, el descarte local queda firme igual (nunca se vuelve a autocargar) y
el Historial lo marca para revisión manual.

resolve_pending corre en cada vista de list_requests (y en cada ciclo del poller
cuando exista) y re-chequea TODAS las filas PENDING contra el nivel en vivo, no solo
las vencidas: si el nivel se recuperó se descarta al toque aunque falte ventana; si
sigue bajo, PENDING hasta el techo (settings.validation_window_hours) y recién ahí
CONFIRMED (se habilita la carga).
"""

import logging
from dataclasses import dataclass

from src.modules.insumos.domain.entities.audit_record import EVENT_AUTO_DISMISSED, AuditRecord
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway, JsonDict
from src.modules.insumos.domain.repositories.order_audit_repository import OrderAuditRepository
from src.modules.insumos.domain.repositories.request_validation_repository import (
    RequestValidationRepository,
)
from src.modules.insumos.domain.services.validation_diagnosis import ValidationDiagnosis
from src.modules.insumos.domain.value_objects.pending_validation import (
    VALIDATION_CONFIRMED,
    VALIDATION_DISMISSED,
    PendingValidationWork,
    ValidationStart,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidationWindowPorts:
    insight: InsightGateway
    validations: RequestValidationRepository
    audit: OrderAuditRepository
    diagnosis: ValidationDiagnosis


class ValidationWindow:
    def __init__(self, ports: ValidationWindowPorts) -> None:
        self._ports = ports

    async def start_pending(
        self,
        request: JsonDict,
        device_id: int,
        customer_id: int,
        device_serial: str,
        deadline_minutes: int,
    ) -> None:
        """Arranca (o no-opea si ya existe y ya se diagnosticó) la ventana de una
        solicitud elegible. El diagnóstico se calcula acá, en el primer llamado, para
        que ya esté visible desde que aparece "Validando" en la UI — si la fila ya
        existe con diagnóstico, no se vuelve a consultar Insight en cada vista."""
        if await self._ports.validations.is_diagnosed(int(request["id"])):
            return
        diagnosis = await self._ports.diagnosis.build(
            device_id, request, device_serial=device_serial
        )
        await self._ports.validations.start(
            ValidationStart(
                hp_request_id=int(request["id"]),
                customer_id=customer_id,
                device_id=device_id,
                device_serial=device_serial,
                sku=request["consumable"]["sku"],
                initial_percent_left=request["consumable"].get("percentLeft"),
                deadline_minutes=deadline_minutes,
                swap_note=diagnosis.swap_note if diagnosis else None,
                diagnosis_headline=diagnosis.headline if diagnosis else None,
                diagnosis_detail=diagnosis.detail if diagnosis else None,
            )
        )

    async def resolve_pending(self, min_percent: int) -> None:
        """Re-chequea TODAS las PENDING contra el nivel en vivo. Se recuperó (nivel >
        min_percent) -> DISMISSED de inmediato (el deadline es un techo, no una espera
        obligatoria). Sigue bajo y venció el techo -> CONFIRMED. Sigue bajo sin vencer
        -> queda PENDING para el próximo ciclo."""
        for row in await self._ports.validations.get_all_pending():
            await self._resolve_row(row, min_percent)

    async def _resolve_row(self, row: PendingValidationWork, min_percent: int) -> None:
        """Fail-closed: si no se puede consultar el equipo, o el SKU ya no aparece
        entre sus consumibles (reemplazo real, equipo dado de baja), la fila queda
        PENDING y se reintenta — nunca se asume nada sin poder confirmarlo."""
        live_percent = await self._live_percent(row)
        if live_percent is None:
            return
        if live_percent > min_percent:
            await self._dismiss(row, live_percent)
        elif row.is_due:
            await self._ports.validations.resolve(row.hp_request_id, VALIDATION_CONFIRMED)
            logger.info(
                "request_validation: solicitud %s confirmada (%s%% en vivo, venció el "
                "techo de la ventana), se habilita la carga",
                row.hp_request_id,
                live_percent,
            )
        # else: sigue baja pero no venció el techo — PENDING, se reintenta después.

    async def _live_percent(self, row: PendingValidationWork) -> float | None:
        try:
            consumables = await self._ports.insight.get_device_consumables(row.device_id)
        except Exception as exc:
            logger.error(
                "request_validation: no se pudo consultar el equipo %s para la "
                "solicitud %s; se reintenta en el próximo ciclo",
                row.device_id,
                row.hp_request_id,
                exc_info=exc,
            )
            return None
        match = next((c for c in consumables if c.get("sku") == row.sku), None)
        if match is None or match.get("percentLeft") is None:
            logger.warning(
                "request_validation: SKU %s no encontrado entre los consumibles en "
                "vivo del equipo %s (solicitud %s); se reintenta en el próximo ciclo",
                row.sku,
                row.device_id,
                row.hp_request_id,
            )
            return None
        return float(match["percentLeft"])

    async def _dismiss(self, row: PendingValidationWork, live_percent: float) -> None:
        # Puede perder la carrera contra otra vista/ciclo resolviendo esta misma fila
        # casi a la vez — si ya la resolvieron, no duplicar el evento en el Historial.
        if not await self._ports.validations.resolve(row.hp_request_id, VALIDATION_DISMISSED):
            return
        initial = row.initial_percent_left
        initial_txt = f"{initial:g}%" if initial is not None else "?"
        detail = (
            f"Nivel se recuperó solo ({initial_txt} → {live_percent:g}%) en la ventana "
            "de validación — probable falla de lectura del sensor, no se creó ningún "
            "pedido"
        )
        detail = await self._delete_in_insight(row.hp_request_id, detail)
        await self._ports.audit.record(
            AuditRecord(
                event=EVENT_AUTO_DISMISSED,
                hp_request_id=row.hp_request_id,
                customer_id=row.customer_id,
                device_serial=row.device_serial,
                sku=row.sku,
                device_id=row.device_id,
                detail=detail,
            )
        )
        logger.info(
            "request_validation: solicitud %s descartada (falsa alarma, %s → %s%%)",
            row.hp_request_id,
            initial_txt,
            live_percent,
        )

    async def _delete_in_insight(self, hp_request_id: int, detail: str) -> str:
        """Da de baja la solicitud en HP SDS con el detalle como comentario — best
        effort: si falla, el descarte local ya quedó firme; solo se anota en el
        Historial para revisión manual (nunca se reintenta la eliminación)."""
        try:
            await self._ports.insight.update_consumable_request(
                request_id=hp_request_id,
                status_update="DELETE",
                comment=f"Descartada automáticamente por SDS Autoloader: {detail}.",
            )
        except Exception as exc:
            logger.error(
                "request_validation: no se pudo eliminar en HP SDS la solicitud %s "
                "tras el descarte automático — queda viva en Insight, revisar "
                "manualmente",
                hp_request_id,
                exc_info=exc,
            )
            return detail + " (no se pudo eliminar la solicitud en HP SDS, revisar manualmente)"
        return detail
