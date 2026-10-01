"use client";

import { useCallback, useEffect, useState } from "react";
import { insumosApi } from "../api/insumos-api";
import { SDS_PILOT_IDS } from "../components/clientes/sds-contacts-section";
import type { SdsContactRow, ZoneContactRow } from "../types";

function errorMsg(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

/** Contactos por zona de un cliente (+ contactos SDS para el piloto). Carga al
 * cambiar `customerId`; `onLoadStart` deja al caller resetear su estado de UI
 * en el mismo tick que arranca la carga. `setContacts` queda expuesto para los
 * updates inmutables de los handlers (guardar/borrar/importar). */
export function useZoneContacts(customerId: number | null, onLoadStart: () => void) {
  const [contacts, setContacts] = useState<ZoneContactRow[]>([]);
  const [sdsContacts, setSdsContacts] = useState<SdsContactRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(
    async (id: number) => {
      // Resetear el estado antes de cargar (dentro de useCallback, no
      // directamente en el body del effect — mismo patrón que use-new-devices.ts).
      setContacts([]);
      setSdsContacts([]);
      onLoadStart();
      setLoading(true);
      setError(null);
      try {
        const data = await insumosApi.getContacts(id);
        setContacts(data);
        if (SDS_PILOT_IDS.has(id)) {
          try {
            const sds = await insumosApi.getSdsContacts(id);
            setSdsContacts(sds);
          } catch {
            setSdsContacts([]);
          }
        }
      } catch (err: unknown) {
        setError(errorMsg(err, "No se pudieron cargar los contactos."));
      } finally {
        setLoading(false);
      }
    },
    [onLoadStart],
  );

  useEffect(() => {
    if (!customerId) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void reload(customerId);
  }, [customerId, reload]);

  return { contacts, setContacts, sdsContacts, loading, error, reload };
}
