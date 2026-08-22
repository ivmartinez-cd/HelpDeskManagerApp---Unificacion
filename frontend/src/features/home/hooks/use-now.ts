"use client";

import { useEffect, useState } from "react";

/** Reloj de baja frecuencia para textos relativos ("hace 3 min", línea
 * "ahora"): un solo setInterval por componente, sin Date.now() en render. */
export function useNow(intervaloMs = 30_000): Date {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), intervaloMs);
    return () => clearInterval(id);
  }, [intervaloMs]);
  return now;
}
