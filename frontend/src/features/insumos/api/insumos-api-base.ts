/** Envelope de paginación del backend (`Page[T]` en
 * `shared/presentation/schemas/pagination.py`). Se declara local a este
 * archivo, igual que en `features/contadores/api/contadores-api.ts` — no hay
 * un tipo compartido y no se quiere acoplar features entre sí.
 *
 * A diferencia de contadores, acá NO se desenvuelve `.items` en el cliente:
 * varias tablas de insumos necesitan el `total` (el de `/alerts` es
 * directamente el contador de escaladas), así que los métodos de listado
 * devuelven el `Page<T>` completo. */
export type { Page } from "@/shared/types/pagination";

/** Parámetros de paginación de cualquier listado del módulo. Todos los
 * endpoints tienen un `size` default generoso (500 en las tablas que filtran
 * client-side, 100 en las paginadas en SQL): omitirlos es lo normal. */
export interface PageParams {
  page?: number;
  size?: number;
}

/** Arma un querystring salteando `undefined`/`null` (mandar `?days=undefined`
 * rompe la validación de FastAPI). Devuelve "" o "?a=1&b=2". */
export function toQuery(
  params: Record<string, string | number | boolean | undefined | null>,
): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export const BASE = "/api/insumos";
