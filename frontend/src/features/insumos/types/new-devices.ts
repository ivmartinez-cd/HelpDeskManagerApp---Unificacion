/** Equipos nuevos (sin monitorear): `GET /api/insumos/new-devices`,
 * `/new-devices/summary`, `PATCH /new-devices/{deviceId}` y
 * `POST /new-devices/sync`. */

/** `NewDeviceRowOut`: equipo de un cliente habilitado que Insight ve pero que
 * todavía no está monitoreado, así que no genera avisos de insumos. */
export interface NewDeviceRow {
  deviceId: number;
  customerId: number;
  customerName: string;
  serial: string;
  model: string;
  zone: string;
  ipAddress: string;
  /** Estado de monitoreo tal como lo reporta Insight. */
  monitorStatus: string;
  /** Cuándo lo descubrió Insight (date-time). */
  discoveryDate?: string | null;
  lastContact?: string | null;
  /** Cuándo lo vio por primera vez ESTA app (date-time). */
  firstSeenAt: string;
  /** Ignorado a mano (p.ej. equipos fuera de contrato): no cuenta en el badge. */
  dismissed: boolean;
  /** Deep link al portal de Insight para darlo de alta. */
  registrationUrl: string;
}

/** `NewDevicesSummaryOut`: solo el contador de pendientes sin ignorar — el
 * badge de la barra lateral. Endpoint aparte para no traerse la tabla. */
export interface NewDevicesSummary {
  pendingCount: number;
}

/** `SyncNewDevicesResponse`: resultado del sync, NO el listado. Después de
 * sincronizar hay que volver a pedir el GET paginado (el legacy devolvía las
 * dos cosas en la misma respuesta). */
export interface SyncNewDevicesResponse {
  newDevices: number;
  pruned: number;
}

export interface DismissDeviceResponse {
  ok: boolean;
}
