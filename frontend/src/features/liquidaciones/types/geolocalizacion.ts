export interface GeocodeCandidato {
  formattedAddress: string;
  latitud: number;
  longitud: number;
  locationType: string;
  tipos: string[];
  partialMatch: boolean;
}

export interface GeocodificarResultado {
  resueltasAuto: number;
  ambiguas: number;
  sinResultados: number;
  sinDireccion: number;
  yaResueltas: number;
  llamadasGoogle: number;
  pendientesPorTope: number;
  sinActividad: number;
}

export type EstadoCoordenadas =
  | "resuelta"
  | "ambigua"
  | "sin_resultados"
  | "sin_direccion"
  | "pendiente";

export interface SucursalCoordenadas {
  sigesSucursalId: number;
  empresaNombre: string;
  sucursalNombre: string;
  direccion: string | null;
  estado: EstadoCoordenadas;
  latitud: number | null;
  longitud: number | null;
  procedencia: string | null;
  formattedAddress: string | null;
  candidatos: GeocodeCandidato[];
}

export interface PreviewFilaKm {
  accion: "crear" | "actualizar";
  tablaKmId: string | null;
  empresaNombre: string;
  sucursalNombre: string;
  coordsOrigen: string;
  latitudDestino: number;
  longitudDestino: number;
  kmsIda: number;
  kmsVuelta: number;
  kmsTotal: number;
  umbralViatico: number;
  aplicaViatico: boolean;
  kmsAFacturar: number;
  kmsRecorridoActual: number | null;
  kmsAFacturarActual: number | null;
}

export interface CalculoKmPreview {
  id: string;
  prestadorId: string;
  filas: PreviewFilaKm[];
  sinUbicar: number;
  sinRuta: number;
  elementosGoogle: number;
  sinActividad: number;
  createdAt: string;
}

export interface AplicarDistanciasResult {
  creadas: number;
  actualizadas: number;
}

export interface PinSospechoso {
  sigesSucursalId: number;
  empresaNombre: string;
  sucursalNombre: string;
  direccion: string;
  latitudSiges: number;
  longitudSiges: number;
  latitudGeocode: number;
  longitudGeocode: number;
  formattedAddress: string;
  locationType: string;
  discrepanciaKm: number;
}

export interface AuditarPinesResult {
  geocodificadas: number;
  yaEnCache: number;
  sinDireccion: number;
  pendientesPorTope: number;
  llamadasGoogle: number;
}

/** Diagnóstico completo del Asistente de KM — GET asistente-km/estado.
 * Lo calcula el backend sin gastar Google; es la única fuente de verdad
 * del semáforo del wizard. */
export interface EstadoAsistenteKm {
  vinculadoSiges: boolean;
  baseConfigurada: boolean;
  baseConCoordenadas: boolean;
  sucursalesActivas: number;
  exClientes: number;
  sucursalesNuevasPorImportar: number;
  filasTablaKm: number;
  sinCoordenadas: number;
  ambiguasPendientes: number;
  filasSinKm: number;
  noEncontradasEnSiges: number;
  pinesSospechososCacheados: number;
  estimacionGeocodificar: number;
  estimacionDistancias: number;
  estimacionAuditarPines: number;
  topePorCorrida: number;
}
