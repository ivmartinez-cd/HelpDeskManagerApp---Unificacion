import type {
  EstadoAsistenteKm, HallazgoTier0, HallazgoTier1, HallazgoTier1b, ItemWorklistTier2,
  PinSospechoso, PropuestaN2Match, ResultadoWorklistTier2, SucursalCoordenadas,
} from "../types/liquidaciones";
import { traducirCodigoTier0 } from "./asistente-km-textos";

/** Composición pura de la bandeja única de pendientes del Asistente de KM a
 * partir de las respuestas de los endpoints existentes (cero backend nuevo).
 * Un ítem = una decisión del operador o una acción en bloque. */

export interface FilaNoEncontrada { empresaNombre: string; sucursalNombre: string }

export interface DatosBandeja {
  estado: EstadoAsistenteKm;
  propuestas: PropuestaN2Match[];
  coordenadas: SucursalCoordenadas[];
  tier0: HallazgoTier0[];
  tier1: HallazgoTier1[];
  tier1b: HallazgoTier1b[];
  worklist: ResultadoWorklistTier2 | null;
  pines: PinSospechoso[];
  /** Solo disponible después de "Traer de Gestión" (lo devuelve el refresco). */
  noEncontradas: FilaNoEncontrada[] | null;
}

export type FuenteEvidencia = "geometria" | "dos_fuentes" | "una_fuente" | "google";

export interface Evidencia {
  fuente: FuenteEvidencia;
  /** Texto llano por defecto. */
  texto: string;
  /** Texto técnico para "ver detalle". */
  detalle: string;
}

export interface PinRoto {
  tipo: "pin_roto";
  key: string;
  sigesSucursalId: number;
  empresaNombre: string;
  sucursalNombre: string;
  domicilio: string | null;
  latitud: number | null;
  longitud: number | null;
  evidencias: Evidencia[];
  /** Presente cuando Google confirmó la discrepancia: habilita "Usar la dirección escrita". */
  pinGoogle: PinSospechoso | null;
  vaAlCsv: boolean;
  /** 0 = más grave. */
  severidad: number;
}

export interface PinesVerificar {
  tipo: "pines_verificar";
  key: string;
  items: ItemWorklistTier2[];
  estimacionGoogle: number;
}

export interface NombreCandidato { tipo: "nombre_candidato"; key: string; propuesta: PropuestaN2Match }
export interface NombreSinCandidato { tipo: "nombre_sin_candidato"; key: string; fila: FilaNoEncontrada }
export interface SinUbicacion { tipo: "sin_ubicacion"; key: string; cantidad: number; estimacionGoogle: number }
export interface UbicacionElegir { tipo: "ubicacion_elegir"; key: string; fila: SucursalCoordenadas }
export interface UbicacionSinResultado { tipo: "ubicacion_sin_resultado"; key: string; fila: SucursalCoordenadas }

export type ItemBandeja =
  | PinRoto | PinesVerificar | NombreCandidato | NombreSinCandidato
  | SinUbicacion | UbicacionElegir | UbicacionSinResultado;

export type FiltroBandeja = "todos" | "pines" | "nombres" | "ubicaciones";

const CATEGORIA: Record<ItemBandeja["tipo"], FiltroBandeja> = {
  pin_roto: "pines",
  pines_verificar: "pines",
  nombre_candidato: "nombres",
  nombre_sin_candidato: "nombres",
  sin_ubicacion: "ubicaciones",
  ubicacion_elegir: "ubicaciones",
  ubicacion_sin_resultado: "ubicaciones",
};

/** Orden de presentación: lo que ya se sabe roto con certeza primero, después
 * las decisiones del operador, después las acciones en bloque, al final lo manual. */
const ORDEN: Record<ItemBandeja["tipo"], number> = {
  pin_roto: 0,
  nombre_candidato: 1,
  ubicacion_elegir: 2,
  pines_verificar: 3,
  sin_ubicacion: 4,
  ubicacion_sin_resultado: 5,
  nombre_sin_candidato: 6,
};

const SEVERIDAD_FUENTE: Record<FuenteEvidencia, number> = {
  google: 0, geometria: 1, dos_fuentes: 2, una_fuente: 3,
};

function claveFila(empresa: string, sucursal: string): string {
  return `${empresa.trim().toLowerCase()}::${sucursal.trim().toLowerCase()}`;
}

function nuevoPin(base: {
  sigesSucursalId: number; empresaNombre: string; sucursalNombre: string;
  domicilio?: string | null; latitud: number | null; longitud: number | null;
}): PinRoto {
  return {
    tipo: "pin_roto",
    key: `pin-${base.sigesSucursalId}`,
    sigesSucursalId: base.sigesSucursalId,
    empresaNombre: base.empresaNombre,
    sucursalNombre: base.sucursalNombre,
    domicilio: base.domicilio ?? null,
    latitud: base.latitud,
    longitud: base.longitud,
    evidencias: [],
    pinGoogle: null,
    vaAlCsv: false,
    severidad: 99,
  };
}

function agregarEvidencia(pin: PinRoto, e: Evidencia): void {
  pin.evidencias.push(e);
  pin.severidad = Math.min(pin.severidad, SEVERIDAD_FUENTE[e.fuente]);
}

function obtenerPin(mapa: Map<number, PinRoto>, base: Parameters<typeof nuevoPin>[0]): PinRoto {
  let pin = mapa.get(base.sigesSucursalId);
  if (!pin) { pin = nuevoPin(base); mapa.set(base.sigesSucursalId, pin); }
  if (pin.latitud === null && base.latitud !== null) { pin.latitud = base.latitud; pin.longitud = base.longitud; }
  if (!pin.domicilio && base.domicilio) pin.domicilio = base.domicilio;
  return pin;
}

function sumarCertezaAbsoluta(mapa: Map<number, PinRoto>, items: ItemWorklistTier2[]): void {
  for (const i of items) {
    const pin = obtenerPin(mapa, i);
    pin.vaAlCsv = true;
    for (const motivo of i.motivos) {
      agregarEvidencia(pin, { fuente: "geometria", texto: traducirCodigoTier0(motivo), detalle: `Tier 0 · ${motivo}` });
    }
  }
}

function sumarDosFuentes(mapa: Map<number, PinRoto>, hallazgos: HallazgoTier1b[]): void {
  for (const h of hallazgos) {
    const pin = obtenerPin(mapa, h);
    pin.vaAlCsv = true;
    agregarEvidencia(pin, {
      fuente: "dos_fuentes",
      texto: `El pin está en ${h.provinciaGeoref}, pero su dirección dice ${h.provinciaDeclarada ?? "otra provincia"}. Dos fuentes independientes lo confirman.`,
      detalle: `Tier 1b · Georef (API del Estado): ${h.provinciaGeoref} · Nominatim/OpenStreetMap: ${h.provinciaNominatim} · ${h.atribucion}`,
    });
  }
}

function sumarUnaFuente(mapa: Map<number, PinRoto>, hallazgos: HallazgoTier1[], confirmados: Set<number>): void {
  for (const h of hallazgos) {
    if (confirmados.has(h.sigesSucursalId)) continue;
    agregarEvidencia(obtenerPin(mapa, h), {
      fuente: "una_fuente",
      texto: `Según datos oficiales el pin cae en ${h.provinciaGeoref}, pero su dirección dice ${h.provinciaDeclarada ?? "otra provincia"}. Falta la segunda opinión.`,
      detalle: `Tier 1 · Georef (API del Estado): ${h.provinciaGeoref} · declarada en Gestión: ${h.provinciaDeclarada ?? "sin dato"}`,
    });
  }
}

function sumarGoogle(mapa: Map<number, PinRoto>, pines: PinSospechoso[]): void {
  for (const p of pines) {
    const pin = obtenerPin(mapa, {
      sigesSucursalId: p.sigesSucursalId, empresaNombre: p.empresaNombre, sucursalNombre: p.sucursalNombre,
      domicilio: p.direccion, latitud: p.latitudSiges, longitud: p.longitudSiges,
    });
    pin.pinGoogle = p;
    pin.vaAlCsv = true;
    agregarEvidencia(pin, {
      fuente: "google",
      texto: `El pin de Gestión está a ${p.discrepanciaKm.toFixed(p.discrepanciaKm >= 10 ? 0 : 1)} km de la dirección escrita (${p.direccion}). Según Google.`,
      detalle: `Tier 2 · Google Geocoding: ${p.formattedAddress} · precisión ${p.locationType}`,
    });
  }
}

export function componerPinesRotos(d: DatosBandeja): PinRoto[] {
  const mapa = new Map<number, PinRoto>();
  sumarGoogle(mapa, d.pines);
  sumarCertezaAbsoluta(mapa, d.worklist?.certezaAbsoluta ?? []);
  sumarDosFuentes(mapa, d.tier1b);
  sumarUnaFuente(mapa, d.tier1, new Set(d.tier1b.map((h) => h.sigesSucursalId)));
  return [...mapa.values()].sort((a, b) => a.severidad - b.severidad || a.empresaNombre.localeCompare(b.empresaNombre));
}

function componerNombres(d: DatosBandeja): ItemBandeja[] {
  const items: ItemBandeja[] = d.propuestas.map((p) => ({ tipo: "nombre_candidato", key: `n2-${p.tablaKmId}`, propuesta: p }));
  if (!d.noEncontradas) return items;
  const conCandidato = new Set(d.propuestas.map((p) => claveFila(p.empresaNombre, p.sucursalNombre)));
  for (const f of d.noEncontradas) {
    const clave = claveFila(f.empresaNombre, f.sucursalNombre);
    if (!conCandidato.has(clave)) items.push({ tipo: "nombre_sin_candidato", key: `n1-${clave}`, fila: f });
  }
  return items;
}

function componerUbicaciones(d: DatosBandeja): ItemBandeja[] {
  const items: ItemBandeja[] = [];
  if (d.estado.sinCoordenadas > 0) {
    items.push({ tipo: "sin_ubicacion", key: "sin-ubicacion", cantidad: d.estado.sinCoordenadas, estimacionGoogle: d.estado.estimacionGeocodificar });
  }
  for (const f of d.coordenadas) {
    if (f.estado === "ambigua") items.push({ tipo: "ubicacion_elegir", key: `u2-${f.sigesSucursalId}`, fila: f });
    else if (f.estado === "sin_resultados" || f.estado === "sin_direccion") {
      items.push({ tipo: "ubicacion_sin_resultado", key: `u3-${f.sigesSucursalId}`, fila: f });
    }
  }
  return items;
}

export function componerBandeja(d: DatosBandeja): ItemBandeja[] {
  const items: ItemBandeja[] = [...componerPinesRotos(d), ...componerNombres(d), ...componerUbicaciones(d)];
  const porVerificar = d.worklist?.requiereVerificacion ?? [];
  if (porVerificar.length > 0) {
    items.push({ tipo: "pines_verificar", key: "pines-verificar", items: porVerificar, estimacionGoogle: d.worklist?.estimacionLlamadasGoogle ?? 0 });
  }
  return items.sort((a, b) => ORDEN[a.tipo] - ORDEN[b.tipo]);
}

export function filtrarBandeja(items: ItemBandeja[], filtro: FiltroBandeja): ItemBandeja[] {
  return filtro === "todos" ? items : items.filter((i) => CATEGORIA[i.tipo] === filtro);
}

export interface ResumenBandeja {
  pinesRotos: number;
  paraGestion: number;
  nombres: number;
  ubicaciones: number;
  pinesPorVerificar: number;
  sinUbicacion: number;
  /** Hay ítems derivados de Nominatim/OpenStreetMap → atribución ODbL obligatoria. */
  muestraOsm: boolean;
}

export function resumirBandeja(items: ItemBandeja[]): ResumenBandeja {
  const r: ResumenBandeja = { pinesRotos: 0, paraGestion: 0, nombres: 0, ubicaciones: 0, pinesPorVerificar: 0, sinUbicacion: 0, muestraOsm: false };
  for (const i of items) {
    if (i.tipo === "pin_roto") {
      r.pinesRotos++;
      if (i.vaAlCsv) r.paraGestion++;
      if (i.evidencias.some((e) => e.fuente === "dos_fuentes")) r.muestraOsm = true;
    } else if (i.tipo === "pines_verificar") r.pinesPorVerificar = i.items.length;
    else if (i.tipo === "sin_ubicacion") r.sinUbicacion = i.cantidad;
    else if (CATEGORIA[i.tipo] === "nombres") r.nombres++;
    else r.ubicaciones++;
  }
  return r;
}

/** Decisiones que, si quedan sin resolver, dejan sucursales sin km. */
export function consecuenciaPendientes(r: ResumenBandeja): string | null {
  const partes: string[] = [];
  if (r.nombres > 0) partes.push(`${r.nombres} nombre${r.nombres !== 1 ? "s" : ""} sin confirmar`);
  if (r.ubicaciones > 0) partes.push(`${r.ubicaciones} ubicaci${r.ubicaciones !== 1 ? "ones" : "ón"} sin elegir`);
  if (r.sinUbicacion > 0) partes.push(`${r.sinUbicacion} sucursal${r.sinUbicacion !== 1 ? "es" : ""} sin ubicación`);
  if (partes.length === 0) return null;
  return `Quedan ${partes.join(", ")}: esas sucursales van a quedar SIN km cuando calcules.`;
}
