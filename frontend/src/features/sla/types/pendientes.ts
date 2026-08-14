export interface PrestadorPendientes {
  id_tecnico: number;
  tecnico: string;
  cantidad: number;
  ids_incidente: number[];
  operador_nombre: string | null;
}

export interface OperadorPendientes {
  operador_nombre: string;
  cantidad: number;
}

export interface PendientesResumen {
  total: number;
  por_prestador: PrestadorPendientes[];
  por_operador: OperadorPendientes[];
  updated_at: string;
}

export interface IncidenteSinCerrar {
  id_incidente: number;
  tecnico: string;
  id_tecnico: number;
  cliente: string;
  sucursal: string;
  modelo: string;
  nro_serie: string;
  fecha_ingreso: string | null;
  fecha_finalizacion: string | null;
  dias_en_estado: number;
}
