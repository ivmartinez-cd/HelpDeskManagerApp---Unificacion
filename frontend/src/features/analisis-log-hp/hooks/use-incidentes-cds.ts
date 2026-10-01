import { useEffect, useState } from "react";
import { analisisLogHpApi } from "../api/analisis-log-hp-api";
import type { CdsIncident } from "../types/analisis-log-hp";

/** Incidentes de Canal Directo del equipo; consulta recién cuando `enabled`.
 * `null` mientras carga; un error se muestra como lista vacía. */
export function useIncidentesCds(serial: string, enabled: boolean) {
  const [incidents, setIncidents] = useState<CdsIncident[] | null>(null);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    analisisLogHpApi.getCdsIncidents(serial)
      .then((data) => { if (!cancelled) setIncidents(data); })
      .catch(() => { if (!cancelled) setIncidents([]); });
    return () => { cancelled = true; };
  }, [serial, enabled]);

  return incidents;
}
