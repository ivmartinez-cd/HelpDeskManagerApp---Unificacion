import { useEffect, useState } from "react";
import { analisisLogHpApi } from "../api/analisis-log-hp-api";

type Alert = Record<string, unknown>;

/** Alertas activas e historial del portal SDS; consulta recién cuando `enabled`.
 * `null` mientras carga; un error deja ambas listas vacías. */
export function useAlertasSds(deviceId: string, enabled: boolean) {
  const [current, setCurrent] = useState<Alert[] | null>(null);
  const [history, setHistory] = useState<Alert[] | null>(null);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    Promise.all([
      analisisLogHpApi.getAlerts(Number(deviceId), true),
      analisisLogHpApi.getAlerts(Number(deviceId), false),
    ])
      .then(([c, h]) => { if (!cancelled) { setCurrent(c); setHistory(h); } })
      .catch(() => { if (!cancelled) { setCurrent([]); setHistory([]); } });
    return () => { cancelled = true; };
  }, [deviceId, enabled]);

  return { current, history };
}
