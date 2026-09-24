export type Semaforo = "VERDE" | "AMARILLO" | "NARANJA" | "ROJO";
export type Coloreo = "AZUL" | "NARANJA" | "NORMAL";
export type EstadoMaquina = "NORMAL" | "BACKUP" | "EN_TRANSITO";
export type Tecnologia = "MONO" | "COLOR";

/** `MetodoEstimacion` del Estimador v1.7 ("NoAplica" = lectura real /
 * pendiente: sin tooltip "Detalle de estimación"). */
export type MetodoEstimacion =
  | "NoAplica"
  | "MedianaTruncadaP80"
  | "MedianaCruda"
  | "EntreReales"
  | "ContadorAnterior"
  | "T4ST_Valor"
  | "T4ST_Proyectado";

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
  // `ContadorAnterior` del legacy: null si el equipo no tiene contador facturado.
  ultimo_facturado_valor: number | null;
  ultimo_facturado_fecha: string | null;
  ultimo_facturado_tipo: number | null;
  es_real: boolean;
  // En una fila real: el contador actual ya cargado (celda "real-cargado").
  estim_propuesto: number | null;
  tipo_toma: number | null;
  impresiones: number | null;
  fuente: string;
  metodo_detalle: string;
  coloreo: Coloreo | null;
  borde_salto_imposible: boolean;
  semaforo: Semaforo;
  requiere_confirmacion: boolean;
  es_clase_sintetica: boolean;
  detalle_parque: DetalleParque | null;
  dias_par_pl: number | null;
  tasa_diaria: number | null;
  dias_proyectados: number | null;
  detalle_calculo: string;
  fecha_toma_actual: string | null;
  editado_por_operador: boolean;
  // `NotaOperador` del motor: va debajo del detalle en el tooltip del estimado.
  guia_operador: string | null;
  metodo: MetodoEstimacion;
  etiqueta_nivel: string;
  t4_sin_revisar: boolean;
  meses_sin_real_en_alerta: boolean;
  // ── Columna Modelo, "Detalle por Modelo" y preselección P/L del panel.
  // Opcionales solo para tolerar un backend anterior sin reiniciar. ──
  estado_maquina_desc?: string | null;
  empresa_actual_desc?: string | null;
  id_art_gen?: number | null;
  id_modo_oper?: number | null;
  ultimo_real_fecha?: string | null;
  ultimo_real_tipo?: number | null;
  real_anterior_fecha?: string | null;
  real_anterior_tipo?: number | null;
  // "Detalle por Modelo histórico": valores de parque de la cascada (T19).
  parque_historico?: ParqueHistorico | null;
}

/** Un nivel de la cascada de parque: N equipos, mediana truncada P80 (el
 * valor que usa el motor, `PromParque_*`) y mediana cruda de referencia. */
export interface NivelParque {
  n: number;
  p80: number | null;
  cruda: number | null;
}

export interface ParqueHistorico {
  cliente_modelo: NivelParque;
  grupo_modelo: NivelParque;
  cliente_tec: NivelParque;
  global_modelo: NivelParque;
}

// Composición del promedio de parque usado (tooltip "Detalle de estimación").
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

/** Banner "Restauramos N decisiones de una sesión anterior". `vigentes_hasta`
 * se manda como `descartar_hasta` al apretar "Descartar y empezar limpio". */
export interface RestauracionDecisiones {
  restauradas: number;
  descartadas: number;
  vigentes_hasta: string | null;
}

export interface TableroProyeccion {
  filas: FilaProyeccion[];
  resumen: ResumenProyeccion;
  restauracion: RestauracionDecisiones;
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
  id_contador: number | null;
  desc_tipo_toma: string;
  para_facturar: boolean;
  // `EsUsableComoCandidate`: solo estas se pueden elegir como P o L.
  usable: boolean;
  // Columna "Valid." (`ValidacionLabel`).
  etiqueta_validacion: string;
  cambio_empresa_vs_anterior: boolean;
  cambio_sucursal_vs_anterior: boolean;
  cambio_anexo_vs_anterior: boolean;
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
  // Botones "Usar T19 (cascada)" / "Usar entre reales" (`PuedeUsar*`).
  puede_usar_cascada: boolean;
  puede_usar_entre_reales: boolean;
}

/** Selección real del proceso que se manda con cada acción del panel. Vacía
 * en el modo ejemplo. */
export interface SeleccionProcesoBody {
  nro_proceso?: number;
  id_grupo_economico?: number;
  id_anexo?: number;
  fecha_objetivo?: string;
  descartar_hasta?: string;
}

/** Contra qué grilla opera el panel: el proceso cargado (vacío = ejemplo) y
 * el corte de "Descartar y empezar limpio" vigente, para que candidatos,
 * vista previa y acciones vean la misma fila que muestra la grilla. */
export interface ContextoProceso {
  solicitud: SolicitudTableroReal | undefined;
  descartarHasta: string | null;
}

export interface RecalcularCandidatoBody extends SeleccionProcesoBody {
  id_maquina: number;
  clase: string;
  partida_fecha: string;
  partida_valor: number;
  partida_tipo_toma: number;
  partida_id_contador: number | null;
  partida_para_facturar: boolean;
  llegada_fecha: string;
  llegada_valor: number;
  llegada_tipo_toma: number;
  llegada_id_contador: number | null;
  llegada_para_facturar: boolean;
}

export type MetodoForzado = "entre_reales" | "cascada_parque";

export interface ForzarMetodoBody extends SeleccionProcesoBody {
  id_maquina: number;
  clase: string;
  metodo: MetodoForzado;
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
  detalle_calculo: string;
  etiqueta_nivel: string;
  metodo: MetodoEstimacion;
  marcas: string[];
  guia_operador: string | null;
  t4_sin_revisar: boolean;
  detalle_parque: DetalleParque | null;
}

/** Lectura elegida como Partida o Llegada, con su `ID_Contador` para que el
 * tablero pueda releerla al restaurar la decisión. */
export interface LecturaElegidaBody {
  fecha: string;
  valor: number;
  tipo_toma: number;
  id_contador: number | null;
  para_facturar: boolean;
}

/** Con `partida` y `llegada`: "Aceptar P/L manual" (con la observación
 * escrita en `nota`). Sin ellas: "Aceptar sugerencia", que no lleva nota. */
export interface AceptarBody extends SeleccionProcesoBody {
  nota?: string | null;
  partida?: LecturaElegidaBody;
  llegada?: LecturaElegidaBody;
}

export interface AccionBody extends SeleccionProcesoBody {
  nota?: string | null;
}

export interface OpcionesExport {
  soloEstimados: boolean;
  descartarHasta: string | null;
}

// Línea de tiempo de un equipo: en `proyeccion-historial.ts`.
export type { HistorialEquipo, HistorialLectura } from "./proyeccion-historial";

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
