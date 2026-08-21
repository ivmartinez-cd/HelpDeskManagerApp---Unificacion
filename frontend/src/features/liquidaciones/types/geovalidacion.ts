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
