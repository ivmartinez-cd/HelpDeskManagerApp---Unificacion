export interface TecnicoVencidos {
  tecnico: string;
  cantidad: number;
  ids_incidente: number[];
}

export interface SlaResumen {
  periodo: number;
  total: number;
  correctos: number;
  vencidos: number;
  pct_correctos: number;
  pct_vencidos: number;
  vencidos_por_tecnico: TecnicoVencidos[];
  updated_at: string;
}

export interface IncidenteVencido {
  id_incidente: number;
  tecnico: string;
  region: string;
  cliente: string;
  sucursal: string;
  modelo: string;
  nro_serie: string;
  fecha_ingreso: string | null;
  fecha_operativo: string | null;
  tiempo: string;
  rango: string;
  sla_horas: number;
  horas_vencido: number;
}
