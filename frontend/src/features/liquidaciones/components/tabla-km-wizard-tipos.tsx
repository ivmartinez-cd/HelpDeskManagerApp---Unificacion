/** Pasos del Asistente de KM. El diagnóstico es la pantalla de entrada y la
 * única fuente de navegación recomendada; los demás se pueden visitar desde
 * el stepper salvo que estén bloqueados por el estado. */
export const PASOS_WIZARD = [
  "diagnostico",
  "importar",
  "ubicar",
  "distancias",
  "pines",
] as const;

export type PasoWizard = (typeof PASOS_WIZARD)[number];

export const LABEL_PASO: Record<PasoWizard, string> = {
  diagnostico: "Diagnóstico",
  importar: "Importar",
  ubicar: "Ubicar",
  distancias: "Distancias",
  pines: "Pines",
};
