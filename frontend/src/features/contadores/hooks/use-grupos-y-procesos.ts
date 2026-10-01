import { useEffect, useState } from "react";
import { proyeccionApi } from "../api/proyeccion-api";
import type { GrupoEconomicoOption, ProcesoOption } from "../types/proyeccion";

/** Combos de la herramienta Estimación en 0: grupos económicos y los procesos
 * del grupo elegido (vacío si no hay grupo). Sin manejo de error, como antes. */
export function useGruposYProcesos(idGrupo: string | null) {
  const [grupos, setGrupos] = useState<GrupoEconomicoOption[]>([]);
  const [procesos, setProcesos] = useState<ProcesoOption[]>([]);

  useEffect(() => {
    void proyeccionApi.listGruposEconomicos().then(setGrupos);
  }, []);

  useEffect(() => {
    if (idGrupo == null) return;
    void proyeccionApi.listProcesos(Number(idGrupo)).then(setProcesos);
  }, [idGrupo]);

  return { grupos, procesosVisibles: idGrupo == null ? [] : procesos };
}
