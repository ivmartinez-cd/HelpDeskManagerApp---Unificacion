import type { RequestRow } from "../../types";

/** Reglas de "esta solicitud ya está atendida" — port de `useSupplyStatus.ts`
 * del legacy. Vive en la carpeta del Dashboard porque es la única pantalla que
 * las usa hoy; si Historial las necesita, se suben a `utils/`.
 *
 * Los tres estados terminales son los literales que devuelve Canal Directo en
 * `supplyStatus` (no hay enum en el backend: viaja como texto libre del SOAP).
 */
export const TERMINAL_SUPPLY_STATES: ReadonlySet<string> = new Set([
  "Entregado",
  "Anulado",
  "Cancelado",
]);

/** Hay un pedido en CD asociado y todavía circulando. */
export function hasActiveSupply(row: RequestRow): boolean {
  return Boolean(row.supplyId && !TERMINAL_SUPPLY_STATES.has(row.supplyStatus ?? ""));
}

/** La solicitud ya tiene pedido propio o un pedido activo en CD: no se carga
 * de nuevo ni entra en la selección de acciones masivas. */
export function isLoaded(row: RequestRow): boolean {
  return Boolean(row.orderId || hasActiveSupply(row));
}

/** Color de avatar del cliente (Patrón 1 del handoff: cuadrado 32×32 con
 * iniciales). Solo colores de la línea Institucional + charcoal — el handoff
 * no define paleta de avatares, así que se rota entre los 3 permitidos de
 * forma estable por `customerId`. */
const AVATAR_COLORS = ["#F7941D", "#58595B", "#3A3A3C"] as const;

export function avatarColorFor(customerId: number): string {
  return AVATAR_COLORS[Math.abs(customerId) % AVATAR_COLORS.length];
}

/** Iniciales del cliente para el avatar (máximo 2 letras). */
export function initialsFor(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return "—";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return `${words[0][0]}${words[1][0]}`.toUpperCase();
}
