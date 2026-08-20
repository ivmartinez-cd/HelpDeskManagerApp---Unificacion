/** Momentos del Asistente de KM (rediseño 2026-08-20, ver
 * docs/liquidaciones/REDISENO_UX_ASISTENTE_KM.md). La intro y la pantalla de
 * chequeos no son momentos del stepper: son la entrada. */
export const MOMENTOS = ["traer", "revisar", "calcular"] as const;

export type Momento = (typeof MOMENTOS)[number];

/** "intro" → "chequeos" (tras Empezar) → momentos → "cierre" (tras aplicar km). */
export type FaseWizard = "intro" | "chequeos" | Momento | "cierre";

export const LABEL_MOMENTO: Record<Momento, string> = {
  traer: "Traer de Gestión",
  revisar: "Revisar pendientes",
  calcular: "Calcular km",
};
