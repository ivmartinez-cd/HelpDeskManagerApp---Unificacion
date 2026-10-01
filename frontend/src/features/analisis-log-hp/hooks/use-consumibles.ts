import { useEffect, useState } from "react";
import { analisisLogHpApi } from "../api/analisis-log-hp-api";

/** Consumibles del equipo en el portal SDS; consulta recién cuando `enabled`.
 * Devuelve `null` mientras carga (o si el resultado es de otro equipo). */
export function useConsumibles(deviceId: string, enabled: boolean) {
  const [result, setResult] = useState<{ deviceId: string; data: Record<string, unknown>[] } | null>(null);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    analisisLogHpApi.getConsumables(Number(deviceId))
      .then((data) => { if (!cancelled) setResult({ deviceId, data }); })
      .catch(() => { if (!cancelled) setResult({ deviceId, data: [] }); });
    return () => { cancelled = true; };
  }, [deviceId, enabled]);

  return result?.deviceId === deviceId ? result.data : null;
}
