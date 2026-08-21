export type EstadoLiquidacion =
  | "abierta"
  | "preliquidada"
  | "recibida"
  | "observada"
  | "aprobada"
  | "cerrada";

export interface Liquidacion {
  id: string;
  prestadorId: string;
  numeroLiquidacion: string | null;
  periodo: string;
  tipoLiquidacion: string;
  nombreArchivo: string | null;
  fechaImportacion: string;
  estado: EstadoLiquidacion;
  totalIncidentes: number;
  totalAlertas: number;
  totalImporte: number;
  conceptoExtra: string | null;
  montoExtra: number | null;
  numeroFactura: string | null;
}

export interface LiquidacionPage {
  items: Liquidacion[];
  total: number;
  page: number;
  size: number;
}

export interface ImportarLiquidacionResult {
  liquidacionId: string;
  totalIncidentes: number;
  totalAlertas: number;
  totalObservaciones: number;
}

export interface ImportExcelMaestroResult {
  prestadorId: string;
  prestadorCreado: boolean;
  spstsCreados: number;
  tarifariosCreados: number;
  tarifariosOmitidos: number;
  tablaKmCreadas: number;
  tablaKmOmitidas: number;
  hojaTablaKm: string | null;
}

export interface Incidente {
  id: string;
  numeroIncidente: string;
  nroSerie: string | null;
  tipo: string;
  empresaNombre: string | null;
  sucursalNombre: string | null;
  fechaCierre: string | null;
  costoServicioCobrado: number;
  cantKmCobrado: number;
  costoTotalCobrado: number;
  costoServicioEsperado: number | null;
  cantKmEsperado: number | null;
  estadoValidacion: string;
  localidadCliente: string | null;
  spstId: string | null;
  urlMaps: string | null;
}

export type EstadoAlerta = "pendiente" | "en_revision" | "resuelta" | "descartada";

export interface Alerta {
  id: string;
  incidenteId: string;
  tipoAlerta: string;
  descripcion: string | null;
  datosContexto: Record<string, unknown> | null;
  riesgo: number;
  estado: EstadoAlerta;
  justificacion: string | null;
  fechaGeneracion: string;
}

/** Regla del motor (catálogo ALT001-009). `tieneEvaluador=false` = existe en
 * el catálogo pero nunca genera alertas (ALT006/007). */
export interface ReglaAlerta {
  id: string;
  codigo: string;
  nombre: string;
  descripcion: string | null;
  activa: boolean;
  riesgoBase: number;
  tieneEvaluador: boolean;
  updatedAt: string;
}

export type EstadoObservacion =
  | "pendiente"
  | "en_revision"
  | "resuelta"
  | "rechazada"
  | "excepcion_aprobada";

export interface Observacion {
  id: string;
  tipoObservacion: string;
  severidad: string;
  titulo: string;
  descripcion: string | null;
  montoCobrado: number;
  montoEsperado: number;
  diferencia: number;
  estado: EstadoObservacion;
  fechaGeneracion: string;
}

export interface LiquidacionDetalle {
  liquidacion: Liquidacion;
  incidentes: Incidente[];
  alertas: Alerta[];
  observaciones: Observacion[];
}
