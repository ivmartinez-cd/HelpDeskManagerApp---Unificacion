// Línea de tiempo de un equipo (DrillDownModal legacy).
export interface HistorialLectura {
  fecha: string;
  valor: number;
  id_tipo_toma: number;
  tipo_toma_desc: string;
  para_facturar: boolean;
  fc_nro_proceso: number | null;
  fc_periodo_hasta: string | null;
  fc_impresiones: number | null;
  fc_periodo_facturacion: string | null;
  es_fc: boolean;
  delta: number | null;
  es_ingreso: boolean;
  es_egreso: boolean;
  es_cambio_empresa: boolean;
  es_cambio_anexo: boolean;
  cambio_empresa_vs_anterior: boolean;
  cambio_sucursal_vs_anterior: boolean;
  cambio_anexo_vs_anterior: boolean;
}

export interface HistorialEquipo {
  lecturas: HistorialLectura[];
}
