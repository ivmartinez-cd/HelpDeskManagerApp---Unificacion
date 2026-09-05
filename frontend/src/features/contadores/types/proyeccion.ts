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
  minimo: number;
  q1: number;
  mediana: number;
  q3: number;
  maximo: number;
  valor_equipo: number;
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
