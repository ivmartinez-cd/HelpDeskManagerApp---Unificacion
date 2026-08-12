/** Equipos offline: `GET /api/insumos/offline-devices`,
 * `/offline-devices/outages`, `/offline-devices/summary`,
 * `POST /offline-devices/verify`, `POST /offline-devices/delete`,
 * `PATCH /offline-devices/{deviceId}`. */

/** `OfflineDeviceOut` — equipo sin reportar +72hs con veredicto de CD. */
export interface OfflineDeviceRow {
  deviceId: number;
  customerId: number;
  customerName: string;
  serial: string;
  model: string;
  zone: string;
  lastContact?: string | null;
  daysOffline?: number | null;
  /** Veredicto de Canal Directo: "BODEGA" | "OTRO_CLIENTE" | "EN_CLIENTE" | "ERROR" | "". */
  cdStatus: string;
  /** Texto libre del veredicto (nombre de cliente, detalle de error, etc.). */
  cdDetail: string;
  cdCheckedAt?: string | null;
  offlineDismissed: boolean;
  /** Pertenece a una caída de colector o salida masiva — excluido de la baja. */
  inMassOutage: boolean;
  /** Candidato a baja: veredicto BODEGA sin outage. */
  deletable: boolean;
}

/** `MassOutageOut` — caída de colector o salida masiva. */
export interface MassOutageRow {
  customerId: number;
  customerName: string;
  /** YYYY-MM-DD del día del evento (UTC). */
  day: string;
  deviceCount: number;
  fleetSize: number;
  /** true: señal real de /api/monitors; false: heurística de respaldo. */
  confirmed: boolean;
  monitorName: string;
  /** Solo en outages heurísticos (confirmed=false): si el colector está online. */
  monitorOnline: boolean;
}

export interface OfflineSummary {
  candidateCount: number;
}

export interface VerifyOfflinePayload {
  limit: number;
  customerId?: number | null;
}

export interface VerifyOfflineResponse {
  checked: number;
  bodega: number;
  otroCliente: number;
  enCliente: number;
  errores: number;
  remaining: number;
}

export interface DeleteOfflinePayload {
  deviceIds: number[];
}

export interface DeleteOfflineResultItem {
  deviceId: number;
  serial: string;
  ok: boolean;
  error?: string | null;
}

export interface DeleteOfflineResponse {
  results: DeleteOfflineResultItem[];
  dryRun: boolean;
}

export interface OfflineDismissResponse {
  ok: boolean;
}
