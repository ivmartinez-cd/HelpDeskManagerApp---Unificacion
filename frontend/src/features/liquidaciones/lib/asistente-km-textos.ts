/** Textos en lenguaje llano del Asistente de KM. Los nombres técnicos
 * (Tier, Georef, Nominatim, ROOFTOP…) viven solo en los "ver detalle"; acá se
 * traduce lo que ve el operador por defecto. */

/** "3 sucursales" / "1 sucursal" — evita el "sucursal(es)" que mostraba el wizard viejo. */
export function plural(n: number, singular: string, pluralForm: string): string {
  return `${n} ${n === 1 ? singular : pluralForm}`;
}

const CODIGO_TIER0: Record<string, string> = {
  fuera_de_argentina: "El pin está fuera de Argentina",
  latlon_invertidas: "Latitud y longitud parecen intercambiadas",
  pin_compartido: "Comparte el pin con otras sucursales de domicilio distinto",
  lejos_de_base: "El pin está muy lejos de la sucursal base del prestador",
  sin_coordenadas: "No tiene ubicación cargada en Gestión",
};

export function traducirCodigoTier0(codigo: string): string {
  return CODIGO_TIER0[codigo] ?? codigo.replaceAll("_", " ");
}

const LOCATION_TYPE: Record<string, string> = {
  ROOFTOP: "ubicación exacta",
  RANGE_INTERPOLATED: "ubicación aproximada",
  GEOMETRIC_CENTER: "centro de la zona",
  APPROXIMATE: "ubicación aproximada",
};

export function traducirPrecisionGoogle(locationType: string): string {
  return LOCATION_TYPE[locationType] ?? locationType.toLowerCase();
}

/** Pin de Gestión vs. dirección escrita, según Google. */
export function describirDiferenciaKm(km: number): string {
  return `${km.toFixed(km >= 10 ? 0 : 1)} km de diferencia`;
}

export function enlaceMaps(latitud: number, longitud: number): string {
  return `https://www.google.com/maps?q=${latitud},${longitud}`;
}

/** Ubicación descripta en llano a partir de la provincia detectada. Para pines
 * fuera del país no hay provincia: se muestra la coordenada cruda. */
export function describirDondeCae(provincia: string | null, latitud: number | null, longitud: number | null): string {
  if (provincia) return provincia;
  if (latitud !== null && longitud !== null) return `${latitud.toFixed(4)}, ${longitud.toFixed(4)}`;
  return "un punto sin provincia conocida";
}

export const ATRIBUCION_ODBL = "Datos de mapa © OpenStreetMap contributors (ODbL)";
