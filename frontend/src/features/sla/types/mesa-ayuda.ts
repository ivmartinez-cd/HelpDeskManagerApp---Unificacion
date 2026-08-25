export interface IncidenteMesaAyuda {
  id_incidente: number;
  fecha_ingreso: string | null;
  tipo: string;
  estado: string;
  cliente: string;
  sucursal: string;
  nro_serie: string;
  modelo: string;
  operador_login: string;
  operador: string;
  dias_transcurridos: number;
  demorado: boolean;
}
