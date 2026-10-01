"use client";

import { useCallback, useEffect, useState } from "react";
import { turnosApi } from "../api/turnos-api";
import type { Casilla, Slot, UserOption } from "../types/turnos";

/** Casillas, franjas y usuarios asignables del ABM de turnos. `alCargar`
 * recibe las casillas en cada carga (el caller ajusta su selección); tiene que
 * ser estable (useCallback) para no re-disparar la carga. */
export function useCasillasData(alCargar: (casillas: Casilla[]) => void) {
  const [casillas, setCasillas] = useState<Casilla[]>([]);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(async () => {
    setLoading(true);
    try {
      const [cList, sList, uList] = await Promise.all([
        turnosApi.listCasillas(),
        turnosApi.listSlots(),
        turnosApi.listAssignableUsers(),
      ]);
      setCasillas(cList);
      setSlots(sList);
      setUsers(uList);
      alCargar(cList);
    } catch (err) {
      console.error("Error al cargar datos de turnos:", err);
    } finally {
      setLoading(false);
    }
  }, [alCargar]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refetch();
  }, [refetch]);

  return { casillas, slots, users, loading, refetch };
}
