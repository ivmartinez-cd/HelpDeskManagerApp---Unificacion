/** Orden estable de franjas por horaInicio: si se re-ordenara en cada
 * render, editar el Inicio de una franja la reubicaba en la lista en medio
 * del tipeo (el input se corría bajo el cursor). Cada franja fija su
 * posición una sola vez, al aparecer; franjas existentes no se mueven. */

import { useMemo, useRef } from "react";
import type { FranjaEditable } from "../types/grilla-variantes";

export function useOrdenEstableFranjas(franjas: FranjaEditable[]): FranjaEditable[] {
  const ordenRef = useRef<Map<string, number>>(new Map());

  return useMemo(() => {
    const orden = ordenRef.current;
    const keysActuales = new Set(franjas.map((f) => f.key));
    for (const key of orden.keys()) {
      if (!keysActuales.has(key)) orden.delete(key);
    }

    const nuevas = franjas
      .filter((f) => !orden.has(f.key))
      .sort((a, b) => a.horaInicio.localeCompare(b.horaInicio));
    const base = orden.size;
    nuevas.forEach((f, i) => orden.set(f.key, base + i));

    return [...franjas].sort((a, b) => (orden.get(a.key) ?? 0) - (orden.get(b.key) ?? 0));
  }, [franjas]);
}
