/** Lecturas de detalle de equipo/consumible — alimentan el modal de detalle
 * que se abre desde la fila expandida del Dashboard.
 *
 * Endpoints:
 *  - `GET /api/insumos/devices/{serial}/supplies`
 *  - `GET /api/insumos/devices/{deviceId}/consumables/{index}/history`
 *  - `GET /api/insumos/devices/{deviceId}/consumables/{index}/requests`
 *  - `GET /api/insumos/devices/{deviceId}/consumables/{index}/detail`
 *  - `GET /api/insumos/devices/{deviceId}/availability-windows`
 *
 * Ninguno viene paginado: son colecciones inline acotadas (top-N o ~12 meses).
 */

/** `DeviceSupplyItemOut` — snake_case en el backend salvo `supplyUrl`; está
 * tipado tal cual llega, no normalizar. */
export interface DeviceSupplyItem {
  supply_id: number;
  supply_id_full: string;
  serial: string;
  estado: string;
  fecha: string;
  sku: string;
  descripcion: string;
  supplyUrl?: string | null;
  /** De dónde salió la fila: SOAP en vivo, cache local o pedido propio. */
  source: string;
}

export interface DeviceSuppliesResponse {
  serial: string;
  supplies: DeviceSupplyItem[];
  dryRun: boolean;
}

/** `ConsumableHistoryPointOut` — `date` es string (no `format: date`, viene
 * del portal tal cual). `level` es el % de nivel, nulo si no hubo lectura. */
export interface ConsumableHistoryPoint {
  date: string;
  level?: number | null;
}

export interface ConsumableHistoryResponse {
  points: ConsumableHistoryPoint[];
}

/** `ConsumableRequestHistoryItemOut`: una solicitud de HP SDS para este
 * consumible, con cualquiera de los 6 workflowStatus del portal. */
export interface ConsumableRequestHistoryItem {
  requestId: number;
  requested: string;
  status: string;
  statusLabel: string;
  reason?: string | null;
  requestedLevel?: number | null;
  requestedDaysLeft?: number | null;
}

export interface ConsumableRequestHistoryResponse {
  items: ConsumableRequestHistoryItem[];
}

/** `AvailabilityWindowOut`: franja de "sin contacto" del EQUIPO, para pintar
 * arriba del gráfico de nivel. */
export interface AvailabilityWindow {
  start: string;
  end: string;
}

export interface AvailabilityWindowsResponse {
  windows: AvailabilityWindow[];
}

/** `ConsumableDetailOut`: datos ampliados EN VIVO de un consumible. TODOS los
 * campos son opcionales (el endpoint tira 404 si el consumible no existe en
 * Insight, pero si existe puede venir incompleto). */
export interface ConsumableDetail {
  model?: string | null;
  type?: string | null;
  colour?: string | null;
  serialNumber?: string | null;
  sku?: string | null;
  adjustedYield?: number | null;
  reorderSku?: string | null;
  reorderYield?: number | null;
  capacity?: number | null;
  percentLeft?: number | null;
  daysLeft?: number | null;
  pagesLeft?: number | null;
  lastRead?: string | null;
  engineCycles?: number | null;
  firstRead?: string | null;
  daysMonitored?: number | null;
  engineCyclesMonitored?: number | null;
}
