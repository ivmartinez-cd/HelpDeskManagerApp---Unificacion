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
  cardParque: boolean; // feature prestadores-card-parque → card "Parque"
  cardEquipo: boolean; // feature vacaciones-card-equipo → "Equipo"
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
  | "proximos-equipo"
  | "parque";

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
  parque: (m) => m.cardParque,
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

export type ViewKey = "hoy" | "seguimiento";

export interface DashboardView {
  key: ViewKey;
  label: string;
  rows: LayoutRow[];
}

/** Fuente de verdad del layout de viewport fijo (≥ xl), en dos vistas
 * (feedback TL 2026-08-22: "mucha info de golpe"): **Hoy** = lo que se opera
 * en el día; **Seguimiento** = lo que se mira cada tanto. La franja de KPIs
 * queda siempre visible arriba de las dos, así el estado global nunca se
 * esconde. Dentro de una vista: filas de alto proporcional; cada fila reparte
 * su ancho entre las cards visibles. Una card sin módulo (o sin novedades,
 * ver card-quiet.ts) desaparece y sus vecinas ocupan su lugar; una fila sin
 * cards desaparece y las demás crecen — nunca queda un hueco. Para mover una
 * card: editar acá, no el componente. */
export const VIEWS: DashboardView[] = [
  {
    key: "hoy",
    label: "Hoy",
    rows: [
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
          { id: "wati-pendientes", w: 4 },
          { id: "insumos", w: 4 },
          { id: "facturacion", w: 4 },
        ],
      },
    ],
  },
  {
    key: "seguimiento",
    label: "Seguimiento",
    rows: [
      {
        h: 1,
        cells: [
          { id: "sla-mes", w: 3.5 },
          { id: "operadores", w: 5.5 },
          { id: "pendientes-cerrar", w: 3 },
        ],
      },
      {
        // Listas cortas: menos alto que la fila de SLA/Operadores.
        h: 0.8,
        cells: [
          { id: "liquidaciones", w: 4 },
          { id: "proximos-equipo", w: 4 },
          { id: "parque", w: 4 },
        ],
      },
    ],
  },
];

/** Filas/celdas visibles de una vista para el acceso dado, sin las cards
 * "sin novedades" (`quiet`) y sin filas vacías. */
export function layoutVisible(
  view: ViewKey,
  access: ModuleAccess,
  quiet: ReadonlySet<CardId> = new Set(),
): LayoutRow[] {
  const vista = VIEWS.find((v) => v.key === view) ?? VIEWS[0];
  return vista.rows
    .map((row) => ({
      ...row,
      cells: row.cells.filter((c) => CARD_GUARDS[c.id](access) && !quiet.has(c.id)),
    }))
    .filter((row) => row.cells.length > 0);
}

/** Cards de una vista que el usuario tiene (con o sin novedades). */
export function cardsDeVista(view: ViewKey, access: ModuleAccess): CardId[] {
  const vista = VIEWS.find((v) => v.key === view) ?? VIEWS[0];
  return vista.rows.flatMap((r) => r.cells.map((c) => c.id)).filter((id) => CARD_GUARDS[id](access));
}
