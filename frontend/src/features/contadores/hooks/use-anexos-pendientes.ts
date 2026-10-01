import { useCallback, useEffect, useState } from "react";
import { contadoresApi } from "../api/contadores-api";
import type {
  AnexoPendiente,
  AnexosPendientesResumen,
  EstadoAnexoPendiente,
} from "../types/anexos-pendientes";

/** Anexos sin facturar + KPIs. Recarga al cambiar el estado o la búsqueda
 * (esta espera 350ms de inactividad). `load(true)` fuerza saltear la caché. */
export function useAnexosPendientes(estado: string, busqueda: string) {
  const [rows, setRows] = useState<AnexoPendiente[] | null>(null);
  const [resumen, setResumen] = useState<AnexosPendientesResumen | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busquedaAplicada, setBusquedaAplicada] = useState("");

  // La búsqueda espera 350ms de inactividad antes de pegarle al backend.
  useEffect(() => {
    const timer = setTimeout(() => setBusquedaAplicada(busqueda.trim()), 350);
    return () => clearTimeout(timer);
  }, [busqueda]);

  const load = useCallback(
    (refresh = false) => {
      const lista = contadoresApi
        .listAnexosPendientes({
          estado: estado === "todos" ? undefined : (estado as EstadoAnexoPendiente),
          search: busquedaAplicada || undefined,
          refresh,
        })
        .then((items) => {
          setRows(items);
          setError(null);
        });
      const kpis = contadoresApi.getAnexosPendientesResumen().then(setResumen);
      return Promise.all([lista, kpis]).catch((err: unknown) => {
        console.error("Error al cargar anexos sin facturar:", err);
        setError("No se pudo consultar. Reintentá en unos segundos.");
      });
    },
    [estado, busquedaAplicada],
  );

  useEffect(() => {
    void load();
  }, [load]);

  return { rows, resumen, error, load };
}
