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
