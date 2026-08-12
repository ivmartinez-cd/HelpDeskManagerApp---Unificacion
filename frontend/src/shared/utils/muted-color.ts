/** Atenúa un color hex mezclándolo con negro en oklch (más parejo
 * perceptualmente que mezclar en sRGB) — para colores que llegan de un
 * sistema externo pensado para fondo claro (ej. Gestión) y que sobre el tema
 * oscuro de esta app quedan demasiado saturados/neón (feedback del usuario,
 * 2026-08-12). Promovido desde `features/contadores/utils/calendario-format.ts`,
 * primer lugar donde apareció el problema. */
export function mutedColor(hex: string): string {
  return `color-mix(in oklch, ${hex} 70%, black)`;
}
