import { useEffect, useState } from "react";
import { analisisLogHpApi } from "../api/analisis-log-hp-api";
import type { ClientDevice, FleetClient } from "../types/analisis-log-hp";

/** Clientes de la flota SDS (para el combo de búsqueda por cliente). */
export function useClientesFlota() {
  const [clients, setClients] = useState<FleetClient[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    analisisLogHpApi.listClients()
      .then((data) => { if (!cancelled) setClients(data); })
      .catch(() => { if (!cancelled) setError("No se pudo cargar la lista de clientes."); });
    return () => { cancelled = true; };
  }, []);

  return { clients, error };
}

/** Equipos del cliente elegido. Al cambiar de cliente vuelve a `null` (cargando);
 * un error se muestra como lista vacía. */
export function useEquiposCliente(customerId: string) {
  const [devices, setDevices] = useState<ClientDevice[] | null>(null);
  const [prevCustomerId, setPrevCustomerId] = useState(customerId);
  if (customerId !== prevCustomerId) {
    setPrevCustomerId(customerId);
    setDevices(null);
  }

  useEffect(() => {
    if (!customerId) return;
    let cancelled = false;
    analisisLogHpApi.getClientDevices(Number(customerId))
      .then((data) => { if (!cancelled) setDevices(data); })
      .catch(() => { if (!cancelled) setDevices([]); });
    return () => { cancelled = true; };
  }, [customerId]);

  return { devices, loading: Boolean(customerId) && devices === null };
}
