export type ColKey = "planificacion" | "contadores" | "sla" | "admin";

export interface ModuleAccess {
  contadores: boolean;
  sla: boolean;
  prestadores: boolean;
  insumos: boolean;
  liquidaciones: boolean;
}

export interface CardDef {
  id: string;
  col: ColKey;
  order: number;
  guard: (m: ModuleAccess) => boolean;
}

/** Fuente de verdad del grid: inicio-dashboard.tsx arma grid-template-columns
 * con las fractions de las columnas visibles (sin tracks para columnas ocultas). */
export const COLUMNS: { key: ColKey; fraction: string }[] = [
  { key: "planificacion", fraction: "1.4fr" },
  { key: "contadores",    fraction: "1fr" },
  { key: "sla",           fraction: "0.9fr" },
  { key: "admin",         fraction: "0.9fr" },
];

export const CARDS: CardDef[] = [
  { id: "turnos",            col: "planificacion", order: 0, guard: ()  => true },
  { id: "clientes-hoy",      col: "planificacion", order: 1, guard: (m) => m.contadores },
  { id: "heatmap-semana",    col: "planificacion", order: 2, guard: (m) => m.contadores },
  { id: "contadores-donut",  col: "contadores",    order: 0, guard: (m) => m.contadores },
  { id: "pendientes-antig",  col: "contadores",    order: 1, guard: (m) => m.contadores },
  { id: "cierre-mensual",    col: "contadores",    order: 2, guard: (m) => m.contadores },
  { id: "sla-mes",           col: "sla",           order: 0, guard: (m) => m.sla },
  { id: "pendientes-cerrar", col: "sla",           order: 1, guard: (m) => m.sla },
  { id: "liquidaciones",     col: "admin",         order: 0, guard: (m) => m.liquidaciones },
  { id: "parque",            col: "admin",         order: 1, guard: (m) => m.prestadores },
  { id: "insumos",           col: "admin",         order: 2, guard: (m) => m.insumos },
];

export function cardsForCol(col: ColKey, access: ModuleAccess): CardDef[] {
  return CARDS.filter((c) => c.col === col && c.guard(access)).sort((a, b) => a.order - b.order);
}
