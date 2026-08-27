import { useEffect, useMemo, useState } from "react";
import { prestadoresApi } from "../api/prestadores-api";
import type { OperadorOption, PrestadoresResumen } from "../types/prestadores";

function matchesSearch(query: string, denComercial: string, razonSocial: string | null): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  return denComercial.toLowerCase().includes(q) || (razonSocial ?? "").toLowerCase().includes(q);
}

export function usePrestadoresHub() {
  const [resumen, setResumen] = useState<PrestadoresResumen | null>(null);
  const [operadores, setOperadores] = useState<OperadorOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const reload = () => {
    return Promise.all([prestadoresApi.getResumen(), prestadoresApi.listOperadores()])
      .then(([r, ops]) => {
        setResumen(r);
        setOperadores(ops);
        setError(null);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar prestadores:", err);
        setError(err instanceof Error ? err.message : "No se pudieron cargar los prestadores.");
      });
  };

  useEffect(() => {
    reload().then(() => setLoading(false));
  }, []);

  const gruposFiltrados = useMemo(() => {
    if (!resumen) return [];
    return resumen.grupos
      .map((g) => ({
        ...g,
        prestadores: g.prestadores.filter((p) => matchesSearch(search, p.denComercial, p.razonSocial)),
      }))
      .filter((g) => g.prestadores.length > 0);
  }, [resumen, search]);

  const handleSync = () => {
    setSyncing(true);
    setSyncMessage(null);
    prestadoresApi
      .syncDesdeSiges()
      .then((result) => {
        setSyncMessage(
          `${result.actualizados.length} actualizados, ${result.sinCambios} sin cambios.`,
        );
        return reload();
      })
      .catch((err: unknown) => {
        console.error("Error al sincronizar desde Siges:", err);
        setSyncMessage(err instanceof Error ? err.message : "No se pudo sincronizar.");
      })
      .finally(() => setSyncing(false));
  };

  return {
    resumen,
    operadores,
    loading,
    error,
    syncing,
    syncMessage,
    search,
    setSearch,
    gruposFiltrados,
    handleSync,
    reload,
  };
}
