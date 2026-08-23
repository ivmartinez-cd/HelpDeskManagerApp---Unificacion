import type { EstadoPreventivo } from "../types/preventivos";
import { ESTADO_COLOR } from "./preventivos-mapa-colores";

// Mismo orden que ORDEN_ESTADO_PRIORIDAD en el backend
// (domain/services/vencimiento.py): menor número = más urgente. Duplicado a
// propósito (constante pura de 5 líneas, no vale la pena compartir entre
// front y back para esto).
const ORDEN_ESTADO_PRIORIDAD: Record<EstadoPreventivo, number> = {
  vencido: 0,
  sin_preventivo: 1,
  por_vencer: 2,
  al_dia: 3,
  sin_frecuencia: 4,
};

export function peorEstadoDe(estados: EstadoPreventivo[]): EstadoPreventivo {
  return estados.reduce((peor, actual) =>
    ORDEN_ESTADO_PRIORIDAD[actual] < ORDEN_ESTADO_PRIORIDAD[peor] ? actual : peor,
  );
}

/** Burbuja de cluster coloreada por el estado más urgente del grupo — mismo
 * criterio que un punto individual (preventivos-mapa-icono.ts), para que
 * agrupar pines no esconda que hay algo vencido adentro. */
export function crearIconoCluster(
  leaflet: typeof import("leaflet"),
  cantidad: number,
  peorEstado: EstadoPreventivo,
): import("leaflet").DivIcon {
  const color = ESTADO_COLOR[peorEstado];
  const tamano = cantidad >= 100 ? 44 : cantidad >= 10 ? 38 : 32;
  const fuente = tamano >= 38 ? 13 : 11;
  return leaflet.divIcon({
    className: "",
    html:
      `<div style="display:flex;align-items:center;justify-content:center;` +
      `width:${tamano}px;height:${tamano}px;border-radius:9999px;background:${color};` +
      `border:2px solid var(--color-card);box-shadow:0 1px 3px rgba(0,0,0,.35);` +
      `color:#fff;font:700 ${fuente}px/1 system-ui,sans-serif;` +
      `text-shadow:0 1px 2px rgba(0,0,0,.35)">${cantidad}</div>`,
    iconSize: [tamano, tamano],
  });
}
