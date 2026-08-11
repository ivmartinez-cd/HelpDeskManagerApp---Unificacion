export interface CalendarEvent {
  id: string;
  title: string;
  start: string;
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
  operador_id?: string;
}
