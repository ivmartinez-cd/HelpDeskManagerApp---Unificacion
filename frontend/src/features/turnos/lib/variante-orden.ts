/** Orden estable de franjas por horaInicio: si se re-ordenara en cada
 * render, editar el Inicio de una franja la reubicaba en la lista en medio
 * del tipeo (el input se corría bajo el cursor). Cada franja fija su
 * posición una sola vez, al aparecer; franjas existentes no se mueven. */

import { useState } from "react";
import type { FranjaEditable } from "../types/grilla-variantes";

export function useOrdenEstableFranjas(franjas: FranjaEditable[]): FranjaEditable[] {
  const [orden, setOrden] = useState<string[]>([]);

  const vigentes = new Set(franjas.map((f) => f.key));
  const conservadas = orden.filter((key) => vigentes.has(key));
  const conocidas = new Set(conservadas);
  const nuevas = franjas
    .filter((f) => !conocidas.has(f.key))
    .sort((a, b) => a.horaInicio.localeCompare(b.horaInicio))
    .map((f) => f.key);
  const siguiente = [...conservadas, ...nuevas];

  // Ajuste de estado durante el render (patrón documentado por React): se
  // vuelve a renderizar de inmediato con el orden ya fijado.
  if (siguiente.length !== orden.length || siguiente.some((key, i) => key !== orden[i])) {
    setOrden(siguiente);
  }

  const posicion = new Map(siguiente.map((key, i) => [key, i]));
  return [...franjas].sort((a, b) => (posicion.get(a.key) ?? 0) - (posicion.get(b.key) ?? 0));
}
