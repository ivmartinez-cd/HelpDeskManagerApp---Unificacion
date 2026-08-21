/** Empaquetado de cards del dashboard en un grid sin scroll.
 *
 * Las cards conservan su alto natural y se reparten en columnas manteniendo
 * el orden del registro (grupos contiguos). Cada fila del grid mide lo que
 * mide su card más alta (filas alineadas), así que el alto total de un
 * reparto es la suma de los máximos por fila — exactamente lo que después
 * dibuja CSS Grid con `grid-row`/`grid-column` explícitos. */

export const MIN_CARD_W = 300;
/** Por encima de este ancho las cards se ven estiradas: si hay altura de
 * sobra se prefiere una columna más antes que cards tan anchas. */
export const MAX_CARD_W = 760;

export interface GridLayout {
  cols: number;
  /** Cantidad de cards por columna, en orden. */
  sizes: number[];
  /** false = ni con el máximo de columnas entra sin scroll (fallback). */
  fits: boolean;
}

export interface ElegirColumnasInput {
  /** Alto natural de cada card, en orden del registro (0 = aún sin medir). */
  heights: number[];
  ancho: number;
  alto: number;
  gap: number;
  /** Piso de histéresis: no volver a probar menos columnas que esto. */
  floorK: number;
  /** Columnas actualmente dibujadas (para detectar overflow medido). */
  colsActual: number;
}

/** Todas las formas de partir n ítems en k grupos contiguos no vacíos. */
function gruposContiguos(n: number, k: number): number[][] {
  if (k <= 1) return [[n]];
  const out: number[][] = [];
  for (let primero = 1; primero <= n - (k - 1); primero++) {
    for (const resto of gruposContiguos(n - primero, k - 1)) out.push([primero, ...resto]);
  }
  return out;
}

function alturaGrid(heights: number[], sizes: number[], gap: number): number {
  const filas = Math.max(...sizes);
  const offsets: number[] = [];
  sizes.reduce((acc, s) => (offsets.push(acc), acc + s), 0);
  let total = 0;
  for (let r = 0; r < filas; r++) {
    let maxFila = 0;
    sizes.forEach((s, c) => {
      if (r < s) maxFila = Math.max(maxFila, heights[offsets[c] + r] ?? 0);
    });
    total += maxFila;
  }
  return total + gap * (filas - 1);
}

/** Reparto de menor alto para k columnas; a igual alto, el más parejo. */
export function mejorReparto(heights: number[], k: number, gap: number) {
  let mejor = { sizes: [heights.length], altura: Number.POSITIVE_INFINITY };
  for (const sizes of gruposContiguos(heights.length, k)) {
    const altura = alturaGrid(heights, sizes, gap);
    const masParejo = altura === mejor.altura && Math.max(...sizes) < Math.max(...mejor.sizes);
    if (altura < mejor.altura || masParejo) mejor = { sizes, altura };
  }
  return mejor;
}

export function anchoColumna(ancho: number, k: number, gap: number): number {
  return (ancho - gap * (k - 1)) / k;
}

/** Elige la menor cantidad de columnas con la que todo entra en `alto`
 * (prefiriendo no pasar de MAX_CARD_W) y devuelve además el piso de
 * histéresis actualizado: si con `colsActual` el contenido medido no entra,
 * no se vuelve a intentar con menos columnas hasta que cambie el contexto. */
export function elegirColumnas(input: ElegirColumnasInput): { layout: GridLayout; floorK: number } {
  const { heights, ancho, alto, gap, colsActual } = input;
  const n = heights.length;
  if (n === 0) return { layout: { cols: 1, sizes: [], fits: true }, floorK: 1 };

  const maxCols = Math.max(1, Math.min(n, Math.floor((ancho + gap) / (MIN_CARD_W + gap))));
  const entra = (k: number) => mejorReparto(heights, k, gap).altura <= alto;

  let floorK = input.floorK;
  if (colsActual < maxCols && !entra(colsActual)) floorK = Math.max(floorK, colsActual + 1);
  floorK = Math.min(floorK, maxCols);

  const candidatos: number[] = [];
  for (let k = floorK; k <= maxCols; k++) if (entra(k)) candidatos.push(k);
  // Menor k que entra sin pasarse de MAX_CARD_W; si todas se pasan, la de
  // más columnas (cards menos estiradas); si ninguna entra, el máximo (scroll).
  const cols =
    candidatos.find((k) => anchoColumna(ancho, k, gap) <= MAX_CARD_W) ??
    candidatos[candidatos.length - 1] ??
    maxCols;
  const reparto = mejorReparto(heights, cols, gap);
  return { layout: { cols, sizes: reparto.sizes, fits: reparto.altura <= alto }, floorK };
}

/** Celda (1-based) de la card `i` según el reparto por columnas. */
export function celdaDe(sizes: number[], i: number): { col: number; row: number } {
  let acumulado = 0;
  for (let c = 0; c < sizes.length; c++) {
    if (i < acumulado + sizes[c]) return { col: c + 1, row: i - acumulado + 1 };
    acumulado += sizes[c];
  }
  return { col: sizes.length + 1, row: 1 };
}

/** Reparto provisorio parejo (antes de medir, o si cambió la cantidad de cards). */
export function repartoParejo(n: number, k: number): number[] {
  const cols = Math.max(1, Math.min(n, k));
  const base = Math.floor(n / cols);
  const extra = n % cols;
  return Array.from({ length: cols }, (_, c) => base + (c < extra ? 1 : 0));
}
