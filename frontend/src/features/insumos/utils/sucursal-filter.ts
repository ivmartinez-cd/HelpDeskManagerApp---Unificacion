import type { RequestRow } from "../types";

/** Separa las filas seleccionadas para "Cargar seleccionados" entre las que se pueden
 * cargar directo y las que tienen aviso de cambio de sucursal (zona con instrucción de
 * entrega distinta a la ubicación del equipo, ej. Arcadium Lithium) — esas quedan afuera
 * del lote para no perder el aviso post-carga. */
export function partitionBySucursalNotice(rows: RequestRow[]): {
  included: RequestRow[];
  excluded: RequestRow[];
} {
  return {
    included: rows.filter((row) => !row.requiereCambioSucursal),
    excluded: rows.filter((row) => row.requiereCambioSucursal),
  };
}
