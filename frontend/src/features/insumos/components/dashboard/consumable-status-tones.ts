import type { StatusTone } from "../shared";

/** Tono de badge para el `status` (NEW/DELETED/ACTIONED/COMPLETED/IGNORED/QUERIED)
 * de una solicitud de HP SDS — ver `_REQUEST_STATUS_LABELS` en
 * `get_consumable_request_history.py`. No es la misma severidad que
 * `toneForStatusKey` (esa es sobre el nivel de tóner de la fila del
 * dashboard); acá es el estado del workflow de la solicitud en el portal. */
export function toneForRequestStatus(status: string | null | undefined): StatusTone {
  switch (status) {
    case "NEW":
      return "activo";
    case "COMPLETED":
      return "ok";
    case "DELETED":
      return "atencion";
    case "ACTIONED":
      return "advertencia";
    default:
      return "neutral";
  }
}

/** Tono de badge para el `Estado` de un pedido en Canal Directo — ver
 * `cd_state.py` (Pendiente/Despachado/Remito Generado/Entregado/Anulado/Cancelado). */
export function toneForSupplyStatus(status: string | null | undefined): StatusTone {
  switch (status) {
    case "Entregado":
      return "ok";
    case "Anulado":
    case "Cancelado":
      return "atencion";
    case "Pendiente":
    case "Despachado":
    case "Remito Generado":
      return "activo";
    default:
      return "neutral";
  }
}
