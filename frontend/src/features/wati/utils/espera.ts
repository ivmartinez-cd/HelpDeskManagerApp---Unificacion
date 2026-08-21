/** Umbrales del semáforo de espera (minutos sin respuesta humana). */
export const ESPERA_ATENCION_MIN = 15;
export const ESPERA_CRITICA_MIN = 60;

export type NivelEspera = "ok" | "atencion" | "critico";

export function nivelEspera(minutos: number): NivelEspera {
  if (minutos >= ESPERA_CRITICA_MIN) return "critico";
  if (minutos >= ESPERA_ATENCION_MIN) return "atencion";
  return "ok";
}

export const COLOR_NIVEL: Record<NivelEspera, string> = {
  ok: "#22c55e",
  atencion: "#eab308",
  critico: "#ef4444",
};

export function textoEspera(minutos: number): string {
  if (minutos < 1) return "recién";
  if (minutos < 60) return `hace ${minutos} min`;
  const horas = Math.floor(minutos / 60);
  const resto = minutos % 60;
  return resto ? `hace ${horas} h ${resto} min` : `hace ${horas} h`;
}

/** Cuánto hace que el backend sincronizó contra WATI; null = nunca. */
export function textoSincronizado(iso: string | null): string {
  if (!iso) return "sin sincronizar todavía";
  const mins = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 2) return "sincronizado hace un momento";
  if (mins < 60) return `sincronizado hace ${mins} min`;
  return `sincronizado hace ${Math.round(mins / 60)} h`;
}

/** Si la última sincronización es más vieja que esto, la card avisa que el
 * dato puede estar desactualizado (job caído o deshabilitado). */
export const SYNC_VENCIDA_MIN = 10;

export function sincronizacionVencida(iso: string | null): boolean {
  if (!iso) return true;
  return Date.now() - new Date(iso).getTime() > SYNC_VENCIDA_MIN * 60000;
}
