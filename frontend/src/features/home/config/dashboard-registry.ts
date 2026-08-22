export interface ModuleAccess {
  contadores: boolean;
  sla: boolean;
  prestadores: boolean;
  insumos: boolean;
  liquidaciones: boolean;
  vacaciones: boolean;
  wati: boolean;
  /** Cards concedibles por usuario como "funciones" (ADR-032): no alcanza con
   * tener el módulo, se tildan en la grilla de permisos. */
  cardParque: boolean; // feature prestadores-card-parque → KPI "Parque"
  cardEquipo: boolean; // feature vacaciones-card-equipo → "Próximos días del equipo"
  cardOperadores: boolean; // feature contadores-card-operadores → barras de "Operadores"
}

export function moduleAccessFrom(
  modules: { key: string }[],
  hasFeature: (f: string) => boolean,
): ModuleAccess {
  const tiene = (k: string) => modules.some((m) => m.key === k);
  return {
    contadores: tiene("contadores"),
    sla: tiene("sla"),
    prestadores: tiene("prestadores"),
    insumos: tiene("insumos"),
    liquidaciones: tiene("liquidaciones"),
    vacaciones: tiene("vacaciones"),
    wati: tiene("wati"),
    cardParque: hasFeature("prestadores-card-parque"),
    cardEquipo: hasFeature("vacaciones-card-equipo"),
    cardOperadores: hasFeature("contadores-card-operadores"),
  };
}

export type CardId =
  | "turnos"
  | "clientes-hoy"
  | "wati-pendientes"
  | "insumos"
  | "facturacion"
  | "operadores"
  | "sla-mes"
  | "pendientes-cerrar"
  | "liquidaciones"
  | "proximos-equipo";

export const CARD_GUARDS: Record<CardId, (m: ModuleAccess) => boolean> = {
  turnos: () => true,
  "clientes-hoy": (m) => m.contadores,
  "wati-pendientes": (m) => m.wati,
  insumos: (m) => m.insumos,
  facturacion: (m) => m.contadores,
  operadores: (m) => m.contadores,
  "sla-mes": (m) => m.sla,
  "pendientes-cerrar": (m) => m.sla,
  liquidaciones: (m) => m.liquidaciones,
  "proximos-equipo": (m) => m.cardEquipo,
};

export interface LayoutCell {
  id: CardId;
  /** Fracción de ancho dentro de la fila (fr). */
  w: number;
}

export interface LayoutRow {
  /** Fracción de alto dentro del cuerpo (fr). */
  h: number;
  cells: LayoutCell[];
}

/** Fuente de verdad del layout de viewport fijo (≥ xl). Tres filas de alto
 * proporcional; cada fila reparte su ancho entre las cards visibles. Una card
 * sin módulo desaparece y sus vecinas ocupan su lugar; una fila sin cards
 * desaparece y las demás crecen — nunca queda un hueco. Para mover una card:
 * editar acá, no el componente. */
export const LAYOUT: LayoutRow[] = [
  {
    h: 1.15,
    cells: [
      { id: "turnos", w: 7 },
      { id: "clientes-hoy", w: 5 },
    ],
  },
  {
    h: 1,
    cells: [
      { id: "wati-pendientes", w: 3 },
      { id: "insumos", w: 3 },
      { id: "facturacion", w: 3.4 },
      { id: "sla-mes", w: 2.6 },
    ],
  },
  {
    h: 1,
    cells: [
      { id: "operadores", w: 4.6 },
      { id: "pendientes-cerrar", w: 3 },
      { id: "liquidaciones", w: 2.2 },
      { id: "proximos-equipo", w: 2.2 },
    ],
  },
];

/** Filas/celdas visibles para el acceso dado (sin filas vacías). */
export function layoutVisible(access: ModuleAccess): LayoutRow[] {
  return LAYOUT.map((row) => ({
    ...row,
    cells: row.cells.filter((c) => CARD_GUARDS[c.id](access)),
  })).filter((row) => row.cells.length > 0);
}
