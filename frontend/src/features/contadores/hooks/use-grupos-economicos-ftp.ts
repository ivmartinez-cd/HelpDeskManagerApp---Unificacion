import { useEffect, useState } from "react";
import { contadoresApi, type GrupoEconomicoFtp } from "../api/contadores-api";

/** Grupos económicos de Siges con usuario FTP; se carga al abrir el modal. */
export function useGruposEconomicosFtp(enabled: boolean) {
  const [grupos, setGrupos] = useState<GrupoEconomicoFtp[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) return;
    let active = true;
    contadoresApi
      .listGruposEconomicosFtp()
      .then((data) => active && setGrupos(data))
      .catch((err: unknown) => {
        if (active)
          setError(
            err instanceof Error
              ? err.message
              : "Error al cargar grupos de Siges",
          );
      });
    return () => {
      active = false;
    };
  }, [enabled]);

  return { grupos, error };
}
