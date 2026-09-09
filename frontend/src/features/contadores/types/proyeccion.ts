export type Semaforo = "VERDE" | "AMARILLO" | "NARANJA" | "ROJO";
export type Coloreo = "AZUL" | "NARANJA" | "NORMAL";
export type EstadoMaquina = "NORMAL" | "BACKUP" | "EN_TRANSITO";
export type Tecnologia = "MONO" | "COLOR";

export interface FilaProyeccion {
  id_maquina: number;
  nro_serie: string;
  empresa: string;
  sucursal: string;
  sector: string;
  modelo: string;
  tecnologia: Tecnologia;
  estado_maquina: EstadoMaquina;
  clase: string;
  meses_sin_real: number | null;
  historico_12: number[];
  prom_6_facturados: number | null;
  ultimo_facturado_valor: number;
  ultimo_facturado_fecha: string;
  ultimo_facturado_tipo: number;
  es_real: boolean;
  estim_propuesto: number | null;
  tipo_toma: number | null;
  impresiones: number | null;
  fuente: string;
  metodo_detalle: string;
  coloreo: Coloreo | null;
  borde_salto_imposible: boolean;
  semaforo: Semaforo;
  requiere_confirmacion: boolean;
  nota_operador: string | null;
  es_clase_sintetica: boolean;
  detalle_parque: DetalleParque | null;
  dias_par_pl: number | null;
  tasa_diaria: number | null;
  dias_proyectados: number | null;
}

// Auditoría del promedio de parque usado (REGLAS_DE_NEGOCIO §12) — alimenta
// el tooltip "Detalle de estimación" (paridad con EstimacionTooltip.razor).
export interface DetalleParque {
  n_equipos: number;
  n_descartados: number;
  es_mediana_truncada: boolean;
  mediana_cruda: number | null;
  media_cruda: number | null;
}

export interface ResumenProyeccion {
  reales: number;
  estimados: number;
  pendientes: number;
  sospechosos: number;
  total: number;
}

export interface TableroProyeccion {
  filas: FilaProyeccion[];
  resumen: ResumenProyeccion;
}

export interface GrupoEconomicoOption {
  id: number;
  descripcion: string;
}

export interface ProcesoOption {
  nro_proceso: number;
  periodo_facturacion: string;
  nombre_anexo: string;
  periodo_hasta: string;
  id_anexo: number;
}

export interface AnexoOption {
  id_anexo: number;
  nombre_anexo: string;
}

export interface SolicitudTableroReal {
  nroProceso: number;
  idGrupoEconomico: number;
  idAnexo: number;
  fechaObjetivo: string;
}

export interface CandidatoLectura {
  fecha: string;
  tipo_toma: number;
  valor: number;
  valido: boolean;
  motivo_invalidez: string | null;
}

export interface BoxplotParque {
  n_equipos: number;
  q1: number | null;
  mediana: number;
  q3: number | null;
  valor_equipo: number | null;
}

export interface CandidatosEquipo {
  id_maquina: number;
  nro_serie: string;
  empresa: string;
  sucursal: string;
  sector: string;
  modelo: string;
  tecnologia: Tecnologia;
  velocidad_ppm: number | null;
  lecturas: CandidatoLectura[];
  boxplot: BoxplotParque | null;
}

export interface RecalcularCandidatoBody {
  id_maquina: number;
  clase: string;
  partida_fecha: string;
  partida_valor: number;
  partida_tipo_toma: number;
  llegada_fecha: string;
  llegada_valor: number;
  llegada_tipo_toma: number;
  // Solo para un equipo real de Siges — identifican qué grilla ya cargada
  // reusar (ver RecalcularCandidatoSigesUseCase en el backend).
  nro_proceso?: number;
  id_grupo_economico?: number;
  id_anexo?: number;
  fecha_objetivo?: string;
}

export type MetodoForzado = "entre_reales" | "cascada_parque";

export interface ForzarMetodoBody {
  id_maquina: number;
  clase: string;
  metodo: MetodoForzado;
  nro_proceso?: number;
  id_grupo_economico?: number;
  id_anexo?: number;
  fecha_objetivo?: string;
}

export interface RecalcularCandidatoResponse {
  estim_propuesto: number | null;
  impresiones: number | null;
  tipo_toma: number | null;
  fuente: string;
  metodo_detalle: string;
  semaforo: Semaforo;
  requiere_confirmacion: boolean;
  dias_par_pl: number | null;
  tasa_diaria: number | null;
  dias_proyectados: number | null;
}

// El último cálculo manual (P/L o método forzado) que el operador vio y
// decide confirmar al aceptar — si se omite, "aceptar" confirma el
// automático (comportamiento de siempre).
export interface AceptarManualBody {
  contador_propuesto: number | null;
  tipo_toma: number | null;
  fuente: string;
  metodo_detalle: string;
}

// Línea de tiempo de un equipo (MODELO_DE_DATOS.md §3.6, DrillDownModal legacy).
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

export interface Receso {
  id: number;
  id_grupo_economico: number;
  id_anexo: number | null;
  fecha_desde: string;
  fecha_hasta: string;
  descripcion: string;
}

export interface CrearRecesoBody {
  id_grupo_economico: number;
  id_anexo: number | null;
  fecha_desde: string;
  fecha_hasta: string;
  descripcion: string;
}
