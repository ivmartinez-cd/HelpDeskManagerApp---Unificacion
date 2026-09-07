export interface DetalleContadorRow {
  empresa: string;
  sucursal: string;
  sector: string | null;
  modelo: string;
  serie: string;
  nombre_clase: string | null;
  fecha_toma_anterior: string | null;
  contador_anterior: number;
  fecha_toma_actual: string | null;
  contador_actual: number;
  impresiones_reales: number;
  estado_maquina: string | null;
  direccion_ip: string | null;
  mascara_ip: string | null;
  falta_contador: boolean;
  tipo: string | null;
}

export interface DetalleContadorProceso {
  cliente: string;
  filas: DetalleContadorRow[];
}
