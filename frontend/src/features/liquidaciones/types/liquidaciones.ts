export type EstadoLiquidacion = "abierta" | "recibida" | "aprobada" | "cerrada";

export interface PrestadorLiquidacion {
  id: string;
  nombre: string;
  nombreCorto: string;
  cuit: string | null;
  region: string | null;
  activo: boolean;
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
