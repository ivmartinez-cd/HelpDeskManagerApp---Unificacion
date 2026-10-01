"use client";

import { useEffect, useState } from "react";

/** Reloj de baja frecuencia para textos relativos ("hace 3 min", línea
 * "ahora"): un solo setInterval por componente, sin Date.now() en render.
 * Arranca en `null` (no `new Date()`) para que el SSR y el primer render del
 * cliente coincidan siempre — si arrancara con la hora real, un SSR viejo
 * (cache de Turbopack, tab en background) puede diferir varias horas de la
 * hora de hidratación y tirar un hydration mismatch estructural (línea
 * "ahora" del timeline, colores por `inHours`) que `suppressHydrationWarning`
 * no cubre. El valor real llega en el próximo tick, después de montar. */
export function useNow(intervaloMs = 30_000): Date | null {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setNow(new Date());
    const id = setInterval(() => setNow(new Date()), intervaloMs);
    return () => clearInterval(id);
  }, [intervaloMs]);
  return now;
}
