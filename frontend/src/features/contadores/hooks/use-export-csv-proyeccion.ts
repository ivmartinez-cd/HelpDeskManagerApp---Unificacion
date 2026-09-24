import { useState } from "react";
import { mensajeError, proyeccionApi } from "../api/proyeccion-api";
import type { ContextoProceso } from "../types/proyeccion";

/** "Exportar CSV" de la grilla (`GrillaEstimacion.ExportarCsv` v1.7): todo
 * el proceso o solo los estimados, sobre la grilla tal como se ve (con el
 * descarte vigente). Solo con un proceso real cargado. */
export function useExportCsvProyeccion(contexto: ContextoProceso) {
  const [exportando, setExportando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const exportar = (soloEstimados: boolean) => {
    if (!contexto.solicitud || exportando) return;
    setExportando(true);
    setError(null);
    proyeccionApi
      .exportarCsv(contexto.solicitud, { soloEstimados, descartarHasta: contexto.descartarHasta })
      .catch((err) => setError(mensajeError(err, "No se pudo generar el CSV.")))
      .finally(() => setExportando(false));
  };
  return { exportando, error, exportar };
}
