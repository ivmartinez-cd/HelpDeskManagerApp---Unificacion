/** Anotación de cobertura de un evento (ADR-013 fase 2, ver
 * CoberturaEventoSchema en calendario_schemas.py): el evento viaja siempre
 * con su operador real; esta anotación dice quién lo cubre efectivamente.
 * El switch "efectivo/real" de la UI solo cambia el render, nunca el set
 * de eventos ni requiere re-fetch. */
export interface CoberturaEvento {
  override_id: string;
  operador_ausente_id: string;
  operador_ausente_nombre: string | null;
  operador_reemplazante_id: string;
  operador_reemplazante_nombre: string | null;
  operador_reemplazante_color: string | null;
  /** ISO YYYY-MM-DD (fecha pura, sin hora) */
  vigente_desde: string;
  vigente_hasta: string;
  alcance_total: boolean;
}

export type CalendarioVerPor = "efectivo" | "real";

export interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  operador_id?: string | null;
  all_day: boolean;
  background_color?: string | null;
  border_color?: string | null;
  type?: string | null;
  tittle_tooltip?: string | null;
  content_tooltip?: string | null;
  string_tipo_evento?: string | null;
  cliente?: string | null;
  vendedor?: string | null;
  fecha_entrega?: string | null;
  fecha_entrega_deseada?: string | null;
  sucursal_entrega?: string | null;
  sucursal_instalacion?: string | null;
  sucursal_despacho?: string | null;
  contacto_entrega?: string | null;
  contacto_instalacion?: string | null;
  bultos?: number | null;
  costo_seguro?: string | null;
  costo_recambio?: string | null;
  cobertura?: CoberturaEvento | null;
}

export interface CalendarFilterParams {
  start: string;
  end: string;
  operador_id?: string | null;
}

export interface MiOperador {
  operador_id: string | null;
  nombre: string | null;
  color: string | null;
}

export interface Operador {
  id: string;
  nombre: string;
  color: string | null;
}

export interface SyncStatus {
  last_synced_at: string | null;
  total_events: number;
}

export interface SyncCalendarioResult {
  operadores_count: number;
  events_count: number;
  range_start: string;
  range_end: string;
  synced_at: string;
}

export interface OperadorClientes {
  operador_id: string;
  operador_nombre: string;
  operador_color: string | null;
  clientes: number;
  /** null cuando Siges no respondió: la card degrada a solo clientes. */
  impresoras: number | null;
  /** Clientes sin cruce contra Siges — sus impresoras no están en la suma. */
  sin_cruce: string[];
}

export interface ResumenClientesOperador {
  desde: string;
  hasta: string;
  total_clientes: number;
  total_impresoras: number | null;
  operadores: OperadorClientes[];
}

export interface ClientesPendientesPeriodo {
  /** YYYYMM del período inmediato anterior. null si Siges no respondió. */
  periodo: string | null;
  /** null si Siges no respondió: no se inventa un cero. */
  cantidad: number | null;
  /** Nombres de los grupos económicos pendientes. null si Siges no respondió. */
  grupos: string[] | null;
}

export interface EmpresaSiges {
  id: number;
  den_comercial: string;
  impresoras: number;
}

/** Fila del detalle de "Anexos sin procesar" (KPI de Inicio): un anexo de
 * Impresión activo sin `Nro_Proceso` del período al que pertenece la visita
 * vencida del cliente en el calendario (ciclo que rota el día 20). */
export interface AnexoSinProcesar {
  id_anexo: number;
  anexo: string;
  grupo: string;
  cliente: string;
  operador_id: string | null;
  fecha_evento: string;
  dias_vencido: number;
  periodo_esperado: string;
  ultimo_periodo_procesado: string | null;
}

/** KPI de Inicio. Si Siges no responde el endpoint devuelve 502 y el hook
 * queda en `error`: el tile debe mostrar "—", nunca un 0 inventado. */
export interface AnexosSinProcesarResumen {
  clientes: number;
  anexos: number;
  consultado_en: string;
}
