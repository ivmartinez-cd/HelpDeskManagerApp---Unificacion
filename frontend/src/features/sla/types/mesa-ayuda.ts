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
  /** Visita de técnico más reciente en la misma sucursal (null = no hay). */
  visita_id_incidente: number | null;
  visita_tecnico: string | null;
  visita_estado: string | null;
  visitas_en_sucursal: number;
}
