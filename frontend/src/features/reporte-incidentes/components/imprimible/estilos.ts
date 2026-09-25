import type { CSSProperties } from "react";

/** Colores literales del reporte imprimible ("tinta sobre papel"). No usan los
 * tokens del tema: la app es oscura por defecto y el PDF tiene que salir claro
 * siempre. Marca: solo naranja y gris institucionales; el resto son neutros. */
export const NARANJA = "#F7941D";
export const GRIS = "#58595B";
export const TINTA = "#1f2023";
export const BORDE = "#e5e5e5";
export const FONDO_SUAVE = "#f7f7f7";

/** Los gráficos reutilizados (TarjetaGrafico, leyenda de la dona) pintan con
 * utilidades de Tailwind (`bg-card`, `text-foreground`…). Tailwind las resuelve
 * con `var(--color-*)`: redefinirlas acá las fija en claro para todo el
 * subárbol, en la página oscura y en el popup. */
const VARIABLES_PAPEL = {
  "--color-background": "#ffffff",
  "--color-card": "#ffffff",
  "--color-foreground": TINTA,
  "--color-card-foreground": TINTA,
  "--color-muted": FONDO_SUAVE,
  "--color-muted-foreground": GRIS,
  "--color-border": BORDE,
} as CSSProperties;

export const ESTILO_RAIZ: CSSProperties = {
  ...VARIABLES_PAPEL,
  width: "210mm",
  padding: "16mm 14mm",
  boxSizing: "border-box",
  backgroundColor: "#ffffff",
  color: TINTA,
  fontFamily: "Arial, Helvetica, sans-serif",
  colorScheme: "light",
};

/** Reglas de impresión: viajan dentro del propio reporte (un `<style>` hijo)
 * porque el popup solo recibe su outerHTML + las hojas de la app. Pisan el
 * `@page` sin márgenes del hook para que las páginas 2+ no toquen el borde. */
export const CSS_IMPRESION = `
@page { size: A4 portrait; margin: 16mm 14mm 22mm 14mm; }
.ri-imprimible, .ri-imprimible * {
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
.ri-imprimible [data-print-card], .ri-bloque, .ri-imprimible tr {
  break-inside: avoid;
  page-break-inside: avoid;
}
.ri-imprimible thead { display: table-header-group; }
.ri-salto { break-before: page; page-break-before: always; }
@media print {
  .ri-imprimible { width: auto !important; padding: 0 !important; }
  .ri-pie { position: fixed; left: 0; right: 0; bottom: 0; background: #ffffff; }
}
`;

export const ESTILO_ETIQUETA: CSSProperties = {
  fontSize: 10,
  fontWeight: 700,
  letterSpacing: "0.06em",
  textTransform: "uppercase",
  color: GRIS,
};
