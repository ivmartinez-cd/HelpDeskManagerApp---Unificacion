import type { EstadoPreventivo } from "../types/preventivos";

// Mismos tokens que ESTADO_META (preventivos-tabla.tsx) via variables CSS
// (reaccionan solas a light/dark, sin duplicar el mapeo a hex). Sin
// dependencia de Leaflet a propósito: la leyenda (SSR normal) y el ícono
// (client-only) necesitan el mismo color, pero solo el ícono necesita `L`.
export const ESTADO_COLOR: Record<EstadoPreventivo, string> = {
  vencido: "var(--color-destructive)",
  por_vencer: "var(--color-warning)",
  al_dia: "var(--color-success)",
  sin_preventivo: "var(--color-brand-orange)",
  sin_frecuencia: "var(--color-muted-foreground)",
};
