import type { Empleado } from "../types/empleados";

/** Como se muestra el empleado en combos y listas: "Nombre Apellido". */
export function nombreCompleto(e: Pick<Empleado, "firstName" | "lastName">): string {
  return `${e.firstName} ${e.lastName}`;
}

/** El backend ordena por apellido; los combos muestran "Nombre Apellido",
 * así que hay que reordenar acá para que se vea A→Z. */
export function ordenarPorNombre<T extends Pick<Empleado, "firstName" | "lastName">>(
  empleados: T[],
): T[] {
  return [...empleados].sort((a, b) => nombreCompleto(a).localeCompare(nombreCompleto(b), "es"));
}
