export type EstadoLiquidacion =
  | "abierta"
  | "preliquidada"
  | "recibida"
  | "observada"
  | "aprobada"
  | "cerrada";

export interface PrestadorLiquidacion {
  id: string;
  nombre: string;
  nombreCorto: string;
  cuit: string | null;
  region: string | null;
  activo: boolean;
  sigesEmpresaId: number | null;
  cdPrestadorId: number | null;
  sigesBaseSucursalId: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface SucursalPropia {
  sigesSucursalId: number;
  descripcion: string;
  latitud: string | null;
  longitud: string | null;
  tieneCoords: boolean;
}

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

export interface Spst {
  id: string;
  prestadorId: string;
  nombre: string;
  domicilio: string | null;
  localidad: string | null;
  provincia: string | null;
  zona: string | null;
  activo: boolean;
  sigesEmpresaId: number | null;
  createdAt: string;
}

// ── Vínculo y sync contra Siges (ADR-014) ──────────────────────────────────

export interface SigesEmpresa {
  sigesEmpresaId: number;
  denComercial: string;
  razonSocial: string | null;
  cuit: string | null;
  tipo: "PST" | "SPST";
}

export interface PropuestaVinculo {
  entidad: "prestador" | "spst";
  localId: string;
  localNombre: string;
  sigesEmpresaId: number;
  sigesDenComercial: string;
}

export interface PropuestasVinculo {
  propuestas: PropuestaVinculo[];
  disponibles: SigesEmpresa[];
}

export interface SyncSigesCambio {
  localId: string;
  localNombre: string;
  campo: string;
  valorAnterior: string | null;
  valorNuevo: string | null;
}

export interface SyncSigesDiferenciaNombre {
  localId: string;
  localNombre: string;
  sigesDenComercial: string;
}

export interface SyncSigesResult {
  dryRun: boolean;
  cambios: SyncSigesCambio[];
  nombresDistintos: SyncSigesDiferenciaNombre[];
  sinCambios: number;
  sinVinculo: string[];
  vinculoRoto: string[];
}

// ── Sync de tarifarios contra Siges (ADR-014 dataset 2) ────────────────────

export interface ZonaSigesEstado {
  prestadorId: string;
  prestador: string;
  descripcionSiges: string;
  /** true con zonaLocal null = mapeada a la zona genérica (sin zona). */
  mapeada: boolean;
  zonaLocal: string | null;
  propuesta: string | null;
  zonasLocales: string[];
}

export interface ZonasSiges {
  zonas: ZonaSigesEstado[];
}

export interface GrupoTarifasCreadas {
  prestador: string;
  tipoServicio: string;
  zona: string | null;
  cantidad: number;
}

export interface ConflictoTarifario {
  prestador: string;
  tipoServicio: string;
  zona: string | null;
  vigenciaDesde: string;
  campo: string;
  valorLocal: number;
  valorSiges: number;
}

export interface ZonaSinMapear {
  prestador: string;
  descripcionSiges: string;
  filas: number;
}

// ── Alta asistida de Tabla KM (ADR-014 dataset 3) ──────────────────────────

export interface SucursalSiges {
  sigesSucursalId: number;
  empresaNombre: string;
  sucursalNombre: string;
  domicilio: string | null;
  localidad: string | null;
  provincia: string | null;
  yaCargada: boolean;
}

export interface SyncTarifariosResult {
  dryRun: boolean;
  creados: number;
  gruposCreados: GrupoTarifasCreadas[];
  conflictos: ConflictoTarifario[];
  sinCambios: number;
  zonasSinMapear: ZonaSinMapear[];
  prestadoresSinVinculo: string[];
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
  latitudDestino: number | null;
  longitudDestino: number | null;
  kmsIda: number | null;
  kmsVuelta: number | null;
  coordsOrigen: string | null;
  geocodeFormattedAddress: string | null;
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
  conceptoExtra: string | null;
  montoExtra: number | null;
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

export interface Alerta {
  id: string;
  incidenteId: string;
  tipoAlerta: string;
  descripcion: string | null;
  datosContexto: Record<string, unknown> | null;
  riesgo: number;
  estado: string;
  fechaGeneracion: string;
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
