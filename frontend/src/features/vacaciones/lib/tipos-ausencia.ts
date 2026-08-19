import type { TipoAusencia } from "../types/vacaciones";

/** Etiquetas y colores semánticos de los tipos de baja (handoff §Colores de
 * tipos de baja). El naranja institucional queda reservado para Vacaciones. */
export const TIPO_AUSENCIA: Record<TipoAusencia, { label: string; color: string }> = {
  BAJA_ENFERMEDAD: { label: "Baja por enfermedad", color: "#0d9488" },
  TRAMITE_PERSONAL: { label: "Trámites personales", color: "#2563eb" },
  HOME_OFFICE: { label: "Home office", color: "#9ca3af" },
  DESCUENTO_DIA: { label: "Descuento día", color: "#ef4444" },
  GUARDIA: { label: "Guardia", color: "#475569" },
  DIA_ESTUDIO: { label: "Examen/estudio", color: "#059669" },
  OTHER: { label: "Otros", color: "#9ca3af" },
};

export const COLOR_VACACIONES = "#F7941D";

/** Opciones del modal (el legacy no ofrecía OTHER en el alta). */
export const TIPOS_SELECCIONABLES: TipoAusencia[] = [
  "DESCUENTO_DIA",
  "BAJA_ENFERMEDAD",
  "TRAMITE_PERSONAL",
  "GUARDIA",
  "DIA_ESTUDIO",
  "HOME_OFFICE",
];
