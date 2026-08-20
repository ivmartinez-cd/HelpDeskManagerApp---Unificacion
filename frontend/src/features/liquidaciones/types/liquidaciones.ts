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
  sigesBaseSucursalId: number | null;
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
  actividadReciente: boolean;
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

export interface PropuestaVinculoSpst {
  tablaKmId: string;
  empresaNombre: string;
  sucursalNombre: string;
  localidadCliente: string | null;
  spstId: string | null;
  spstNombre: string | null;
}

export interface ResultadoVinculoTablaKmSpst {
  dryRun: boolean;
  totalSinVincular: number;
  conPropuesta: number;
  sinPropuesta: number;
  vinculadas: number;
  ejemplos: PropuestaVinculoSpst[];
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

/** Matching de sucursales Tabla KM ↔ Siges (Fase 1): N1 auto-vinculable
 * (símbolo/abreviatura) y N2 con candidatos difusos que siempre requieren
 * confirmación humana. */
export interface VinculoN1Aplicado {
  tablaKmId: string;
  empresaNombre: string;
  sucursalNombre: string;
  sigesSucursalId: number;
}

export interface ResultadoAutoVinculoN1 {
  vinculadas: number;
  sinCambios: number;
  detalle: VinculoN1Aplicado[];
}

export interface CandidatoN2Match {
  sigesSucursalId: number;
  sucursalNombre: string;
  domicilio: string | null;
  score: number;
  motivo: string;
  /** Misma dirección normalizada que la fila local (sucursal renombrada). */
  mismaDireccion: boolean;
}

export interface PropuestaN2Match {
  tablaKmId: string;
  empresaNombre: string;
  sucursalNombre: string;
  candidatos: CandidatoN2Match[];
}

/** Tier 0 de geovalidación (Fase 2): saneo geométrico sin costo, corre sobre
 * todas las sucursales activas del PST. */
export interface HallazgoTier0 {
  sigesSucursalId: number;
  empresaNombre: string;
  sucursalNombre: string;
  domicilio: string | null;
  latitud: number | null;
  longitud: number | null;
  severidad: "alta" | "media" | "baja";
  codigo: string;
  detalle: string;
}

/** Tier 1 de geovalidación: reverse geocoding de Georef (gratis) comparado
 * contra la provincia declarada en Siges. */
export interface ResultadoConsultarGeoref {
  consultadas: number;
  yaEnCache: number;
  sinCoordenadas: number;
  pendientesPorTope: number;
}

export interface HallazgoTier1 {
  sigesSucursalId: number;
  empresaNombre: string;
  sucursalNombre: string;
  provinciaDeclarada: string | null;
  provinciaGeoref: string;
  latitud: number;
  longitud: number;
}

/** Tier 1b: segunda opinión de Nominatim, solo sobre lo que Georef ya marcó
 * incompatible. Dos fuentes de acuerdo = confirmado, sin gastar Google. */
export interface ResultadoConsultarNominatim {
  consultadas: number;
  yaEnCache: number;
  pendientesPorTope: number;
}

export interface HallazgoTier1b {
  sigesSucursalId: number;
  empresaNombre: string;
  sucursalNombre: string;
  provinciaDeclarada: string | null;
  provinciaGeoref: string;
  provinciaNominatim: string;
  latitud: number;
  longitud: number;
  atribucion: string;
}

/** Worklist final (Tier 2): residuo real tras Tier 0+1+1b. */
export interface ItemWorklistTier2 {
  sigesSucursalId: number;
  empresaNombre: string;
  sucursalNombre: string;
  domicilio: string | null;
  motivos: string[];
  latitud: number | null;
  longitud: number | null;
}

export interface ResultadoWorklistTier2 {
  certezaAbsoluta: ItemWorklistTier2[];
  requiereVerificacion: ItemWorklistTier2[];
  estimacionLlamadasGoogle: number;
}
