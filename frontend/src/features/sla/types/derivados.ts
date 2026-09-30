export interface IncidenteDerivado {
  id_incidente: number;
  fecha_ingreso: string | null;
  tipo: string;
  estado: string;
  cliente: string;
  sucursal: string;
  nro_serie: string;
  modelo: string;
  tecnico: string;
  id_tecnico: number;
  operador: string | null;
  dias_desde_ingreso: number;
  demorado: boolean;
  /** Caso abierto de Mesa de Ayuda en la misma sucursal (null = no hay). */
  mda_id_incidente: number | null;
  casos_mda_en_sucursal: number;
}
