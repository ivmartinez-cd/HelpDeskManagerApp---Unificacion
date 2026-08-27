/** Asistente de alta de prestador — cruza dos módulos independientes sin FK entre
 * sí (liquidaciones.prestadores y prestadores.prestador, ver investigación
 * 2026-08-24): por eso el asistente vive en su propia feature en vez de
 * meterse dentro de `features/liquidaciones` o `features/prestadores` —
 * ninguna feature del repo importa hoy la api/ de otra, y este asistente
 * necesita las dos. Solo cubre el alta de la empresa/PST; el vínculo Siges de
 * técnicos-persona (módulo vacaciones) es un flujo aparte. */

export type PasoAlta = "datos" | "siges" | "base" | "cd" | "sla";

export const PASOS: PasoAlta[] = ["datos", "siges", "base", "cd", "sla"];

export const LABEL_PASO: Record<PasoAlta, string> = {
  datos: "Datos",
  siges: "Siges",
  base: "Base",
  cd: "Canal Directo",
  sla: "Módulo SLA",
};
