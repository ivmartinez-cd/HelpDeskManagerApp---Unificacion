"use client";

import { useCallback, useEffect, useState } from "react";

/** Lista de un solo prestador (acuerdos, tarifas, Tabla KM): sin prestador no
 * pide nada. `loading` se deriva de que lo cargado corresponda a otro
 * prestador, sin setState sincrónico en el effect (prohibido por
 * react-hooks/set-state-in-effect). `fetcher` tiene que ser estable. */
export function useListaPorPrestador<T>(prestadorId: string, fetcher: (prestadorId: string) => Promise<T[]>) {
  const [items, setItems] = useState<T[]>([]);
  const [cargadoPstId, setCargadoPstId] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    if (!prestadorId) return;
    try {
      setItems(await fetcher(prestadorId));
    } finally {
      setCargadoPstId(prestadorId);
    }
  }, [prestadorId, fetcher]);

  useEffect(() => { void refetch(); }, [refetch]);

  return { items, loading: prestadorId !== "" && prestadorId !== cargadoPstId, refetch };
}
