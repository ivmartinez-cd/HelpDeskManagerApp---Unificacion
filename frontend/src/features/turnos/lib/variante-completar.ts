import type { FranjaEditable } from "../types/grilla-variantes";
import type { Slot } from "../types/turnos";
import { diasActivosDeRango } from "./variante-validacion";

export interface Completado {
  franjas: FranjaEditable[];
  /** Días (0=lunes) que se agregaron copiando `diaOrigen`; vacío = sin cambios. */
  agregados: number[];
  diaOrigen: number | null;
}

/** Mientras rige, la variante reemplaza a la titular en todos los días del
 * rango: un día sin franjas se ve vacío en Turnos del día. "Ajustar turnos de
 * hoy" arma un solo día y extender el "hasta" dejaba el resto sin nada, así
 * que los días del rango que la titular cubre y la variante no se completan
 * copiando el día ya armado (`diaBase` si tiene franjas; si no, el primero
 * del rango que tenga). Sin franjas no hay qué copiar: eso es "Precargar". */
export function completarDiasDelRango(
  franjas: FranjaEditable[],
  desde: string,
  hasta: string,
  titular: Slot[],
  diaBase: number,
  nuevaKey: () => string,
): Completado {
  const sinCambios = { franjas, agregados: [], diaOrigen: null };
  if (!rangoCompleto(desde, hasta)) return sinCambios;
  const enRango = diasActivosDeRango(desde, hasta);
  const aplica = (d: number) => !enRango || enRango.has(d);
  const conFranjas = new Set(franjas.map((f) => f.diaSemana));
  const origen = conFranjas.has(diaBase) && aplica(diaBase)
    ? diaBase
    : [...conFranjas].filter(aplica).sort((a, b) => a - b)[0];
  const faltantes = [...new Set(titular.map((s) => s.diaSemana))]
    .filter((d) => aplica(d) && !conFranjas.has(d))
    .sort((a, b) => a - b);
  if (origen === undefined || faltantes.length === 0) return sinCambios;
  const base = franjas.filter((f) => f.diaSemana === origen);
  const copias = faltantes.flatMap((d) => base.map((f) => ({ ...f, key: nuevaKey(), diaSemana: d })));
  return { franjas: [...franjas, ...copias], agregados: faltantes, diaOrigen: origen };
}

/** Un `<input type="date">` emite fechas intermedias mientras se tipea el año
 * (0002-…, 0020-…): no completar sobre esos rangos transitorios. */
function rangoCompleto(desde: string, hasta: string): boolean {
  return desde >= "2000-01-01" && hasta >= desde;
}
