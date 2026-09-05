// ── Alta asistida de Tabla KM (ADR-014 dataset 3) ──────────────────────────

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
  latitudDestino: number | null;
  longitudDestino: number | null;
  kmsIda: number | null;
  kmsVuelta: number | null;
  coordsOrigen: string | null;
  geocodeFormattedAddress: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface PropuestaVinculoSpst {
  tablaKmId: string;
  empresaNombre: string;
  sucursalNombre: string;
  localidadCliente: string | null;
  spstId: string | null;
  spstNombre: string | null;
  /** "localidad" | "provincia" | null — cómo se llegó al SPST propuesto. */
  criterio: string | null;
}

export interface ResultadoVinculoTablaKmSpst {
  dryRun: boolean;
  totalSinVincular: number;
  conPropuesta: number;
  sinPropuesta: number;
  vinculadas: number;
  ejemplos: PropuestaVinculoSpst[];
  /** Propuestas que salieron solo por provincia: se aplican únicamente con
   * `incluirProvincia=true`. */
  porProvincia: number;
}
