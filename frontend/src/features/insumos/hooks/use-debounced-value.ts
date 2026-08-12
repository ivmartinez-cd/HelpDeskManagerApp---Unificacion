"use client";

import { useEffect, useState } from "react";

/** Debounce genérico de un valor. Hoy el único consumidor es la búsqueda de
 * texto del Historial de auditoría (`historial-view.tsx`), que lo usa para no
 * pegarle a `GET /api/insumos/audit` en cada tecla — el input sigue mostrando
 * el valor inmediato, solo el query al backend se retrasa.
 *
 * Se muda a `shared/hooks/` cuando aparezca un segundo consumidor fuera de
 * insumos (no existe ese directorio todavía en el repo).
 *
 * El `setState` dentro del `setTimeout` no es una escritura síncrona del
 * efecto (corre en un tick posterior, cuando el timer vence), así que no cae
 * bajo la regla `react-hooks/set-state-in-effect` — no hace falta el patrón
 * `queueMicrotask` de `use-request-alerts.ts` ni un `eslint-disable`. */
export function useDebouncedValue<T>(value: T, delayMs = 350): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const handle = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(handle);
  }, [value, delayMs]);

  return debounced;
}
