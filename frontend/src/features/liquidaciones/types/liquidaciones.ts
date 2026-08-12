export type EstadoLiquidacion = "abierta" | "recibida" | "aprobada" | "cerrada";

export interface PrestadorLiquidacion {
  id: string;
  nombre: string;
  nombreCorto: string;
  cuit: string | null;
  region: string | null;
  activo: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface Spst {
  id: string;
  prestadorId: string;
  nombre: string;
  domicilio: string | null;
  localidad: string | null;
  provincia: string | null;
  zona: string | null;
  activo: boolean;
  createdAt: string;
}

export interface Tarifario {
  id: string;
  prestadorId: string;
  tipoServicio: string;
  zona: string | null;
  costoServicio: number;
  costoKm: number;
  vigenciaDesde: string;
  vigenciaHasta: string | null;
  createdAt: string;
}

export interface TablaKm {
  id: string;
  prestadorId: string;
  spstId: string | null;
  empresaNombre: string;
  sucursalNombre: string;
  observaciones: string | null;
  domicilioCliente: string | null;
  localidadCliente: string | null;
  provinciaCliente: string | null;
  kmsRecorrido: number;
  umbralViatico: number;
  aplicaViatico: boolean;
  kmsAFacturar: number;
  urlMaps: string | null;
  createdAt: string;
  updatedAt: string;
}

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
