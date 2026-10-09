import type { Saldo } from "../types/empleados";

/** Días que corresponden en el ciclo: por antigüedad más el arrastre del año
 * anterior. El ajuste de la carga inicial no se suma: ya está descontado en
 * `available`, y sumarlo haría que el total no coincida con la antigüedad. */
export function diasDelCiclo(s: Pick<Saldo, "annual" | "carryOver">): number {
  return s.annual + s.carryOver;
}
