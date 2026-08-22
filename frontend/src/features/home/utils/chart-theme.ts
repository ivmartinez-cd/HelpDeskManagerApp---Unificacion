/** Colores de Chart.js resueltos desde los tokens del tema (globals.css).
 * Chart.js pinta en canvas y no entiende clases de Tailwind ni `var(--x)`,
 * así que se leen los valores computados en el momento de dibujar; el
 * componente vuelve a llamar cuando cambia `resolvedTheme`. */
export interface ChartTheme {
  tick: string;
  grid: string;
  orange: string;
}

export const BRAND_ORANGE = "#F7941D";

export function chartTheme(): ChartTheme {
  if (typeof document === "undefined") {
    return { tick: "#8a8a8a", grid: "#dddddd", orange: BRAND_ORANGE };
  }
  const s = getComputedStyle(document.documentElement);
  const leer = (nombre: string, fallback: string) => s.getPropertyValue(nombre).trim() || fallback;
  return {
    tick: leer("--chart-tick", "#8a8a8a"),
    grid: leer("--chart-grid", "#dddddd"),
    orange: BRAND_ORANGE,
  };
}
