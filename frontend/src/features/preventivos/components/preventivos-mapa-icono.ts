import type { EstadoPreventivo } from "../types/preventivos";
import { ESTADO_COLOR } from "./preventivos-mapa-colores";

/** Pin como círculo de color (no el marcador de imagen default de Leaflet:
 * sus assets no resuelven bien con el bundler de Next). Vencido se dibuja
 * más grande — es el que hay que ver primero en un mapa con cientos de puntos.
 * Recibe `leaflet` ya cargado (import dinámico en preventivos-mapa-canvas.tsx):
 * un `import` estático de "leaflet" acá rompe el build de producción (next
 * build con Turbopack evalúa igual el módulo del lado del servidor y explota
 * con "window is not defined", incluso detrás de next/dynamic ssr:false). */
export function crearIconoPunto(
  leaflet: typeof import("leaflet"),
  estado: EstadoPreventivo,
): import("leaflet").DivIcon {
  const color = ESTADO_COLOR[estado];
  const tamano = estado === "vencido" ? 18 : 13;
  const mitad = tamano / 2;
  return leaflet.divIcon({
    className: "",
    html:
      `<span style="display:block;width:${tamano}px;height:${tamano}px;` +
      `border-radius:9999px;background:${color};` +
      `border:2px solid var(--color-card);box-shadow:0 1px 3px rgba(0,0,0,.35)"></span>`,
    iconSize: [tamano, tamano],
    iconAnchor: [mitad, mitad],
  });
}
