/** Parámetros de operación: `GET /api/insumos/config` y `PUT /api/insumos/config`.
 *
 * El PUT responde **200 siempre**: los rangos inválidos vuelven como
 * `ok: false` + `error` para mostrar en el formulario (igual que el legacy),
 * no como 422. Ramificar por `response.ok`, no esperar `ApiError`.
 */

/** `ConfigResponse`: todos los campos son requeridos en la lectura. */
export interface InsumosConfig {
  /** Umbrales de severidad en días restantes de consumible. */
  thresholdCritical: number;
  thresholdUrgent: number;
  thresholdWarning: number;
  /** Auto-carga de pedidos sin intervención del operario. */
  autoloadEnabled: boolean;
  autoloadMaxDays: number;
  autoloadMinPercent: number;
  /** Horas que se espera el cambio de consumible antes de marcar el pedido
   * como no validado. */
  validationWindowHours: number;
  /** Días sin lectura para considerar el nivel "viejo" (`isStaleOffline`). */
  staleDeviceDays: number;
  offlineDeviceHours: number;
  offlineMonitorHours: number;
  /** Mínimos para diagnosticar una caída general del cliente en vez de
   * equipos sueltos offline. */
  offlineOutageMinDevices: number;
  offlineOutageMinPercent: number;
  /** Minutos sin cargar una solicitud antes de escalar la alerta. */
  alertEscalationMinutes: number;
  alertWorkHoursEnabled: boolean;
  alertWorkHourStart: number;
  alertWorkHourEnd: number;
  logisticsMailTo: string[];
  /** Destinatarios de alertas TÉCNICAS (poller de fondo caído/recuperado) —
   * separado a propósito de logisticsMailTo, que es negocio (avisos de
   * despacho). Nunca debe quedar vacío: ver settings_validation.py. */
  opsAlertMailTo: string[];
}

/** `ConfigRequestBody`: el formulario manda el objeto completo, pero todos los
 * campos tienen default de negocio en el backend — un campo ausente cae en ese
 * default, no en 0. Por eso el payload es `Partial`. */
export type InsumosConfigPayload = Partial<InsumosConfig>;

export interface SaveConfigResponse {
  ok: boolean;
  error?: string | null;
}
