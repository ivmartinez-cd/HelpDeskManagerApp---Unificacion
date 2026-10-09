import type { Saldo } from "../types/empleados";

/** Explicación del ajuste para tooltips: de dónde sale y qué significa el signo. */
export const AYUDA_AJUSTE_INICIAL =
  "Diferencia anotada en la planilla de RRHH al empezar a usar el sistema: " +
  "negativo = días ya tomados antes, positivo = días arrastrados del año anterior.";

/** Días que corresponden en el ciclo: por antigüedad más el arrastre del año
 * anterior. El ajuste de la carga inicial se muestra aparte (ver
 * `textoAjusteInicial`) para que el total no parezca un error de antigüedad. */
export function diasDelCiclo(s: Pick<Saldo, "annual" | "carryOver">): number {
  return s.annual + s.carryOver;
}

/** "ajuste inicial −14" / "ajuste inicial +7", o null si no hay ajuste. */
export function textoAjusteInicial(s: Pick<Saldo, "ajusteInicial">): string | null {
  const ajuste = s.ajusteInicial ?? 0;
  if (ajuste === 0) return null;
  const signo = ajuste > 0 ? "+" : "−";
  return `ajuste inicial ${signo}${Math.abs(ajuste)}`;
}

/** Agrega " · ajuste inicial ±N" a un texto cuando el saldo tiene ajuste. */
export function conAjusteInicial(texto: string, s: Pick<Saldo, "ajusteInicial">): string {
  const ajuste = textoAjusteInicial(s);
  return ajuste ? `${texto} · ${ajuste}` : texto;
}
