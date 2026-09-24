import { useEffect, useMemo, useState } from "react";
import { mensajeError, proyeccionApi } from "../api/proyeccion-api";
import type { GrupoEconomicoOption, ProcesoOption, SolicitudTableroReal } from "../types/proyeccion";

/** Combos de `Index.razor` (Estimador v1.7): grupo económico, proceso del
 * grupo y fecha objetivo (al elegir un proceso toma su `PeriodoHasta`).
 * `alCambiar` avisa que la selección cambió: la grilla se limpia y hay que
 * volver a Cargar, como en el legacy. */

function useGrupos(setErrorConexion: (e: string | null) => void) {
  const [grupos, setGrupos] = useState<GrupoEconomicoOption[]>([]);
  useEffect(() => {
    proyeccionApi
      .listGruposEconomicos()
      .then(setGrupos)
      .catch((err) => setErrorConexion(mensajeError(err, "No se pudieron leer los grupos económicos.")));
  }, [setErrorConexion]);
  return grupos;
}

function useProcesos(idGrupo: string | null, setErrorConexion: (e: string | null) => void) {
  const [procesos, setProcesos] = useState<ProcesoOption[]>([]);
  useEffect(() => {
    if (idGrupo == null) return;
    proyeccionApi
      .listProcesos(Number(idGrupo))
      .then(setProcesos)
      .catch((err) => setErrorConexion(mensajeError(err, "No se pudieron leer los procesos del grupo.")));
  }, [idGrupo, setErrorConexion]);
  return idGrupo == null ? [] : procesos;
}

function solicitudDe(idGrupo: string | null, proceso: ProcesoOption | undefined, fecha: string) {
  if (!idGrupo || !proceso || !fecha) return undefined;
  const solicitud: SolicitudTableroReal = {
    nroProceso: proceso.nro_proceso,
    idGrupoEconomico: Number(idGrupo),
    idAnexo: proceso.id_anexo,
    fechaObjetivo: fecha,
  };
  return solicitud;
}

export function useCombosProyeccion(alCambiar: () => void) {
  const [errorConexion, setErrorConexion] = useState<string | null>(null);
  const [idGrupo, setIdGrupo] = useState<string | null>(null);
  const [idProceso, setIdProceso] = useState<string | null>(null);
  const [fechaObjetivo, setFechaObjetivo] = useState("");
  const grupos = useGrupos(setErrorConexion);
  const procesosVisibles = useProcesos(idGrupo, setErrorConexion);
  const procesoElegido = procesosVisibles.find((p) => String(p.nro_proceso) === idProceso);
  const solicitudActual = useMemo(
    () => solicitudDe(idGrupo, procesoElegido, fechaObjetivo),
    [idGrupo, procesoElegido, fechaObjetivo],
  );
  const elegirGrupo = (id: string | null) => {
    setIdGrupo(id);
    setIdProceso(null);
    setErrorConexion(null);
    alCambiar();
  };
  const elegirProceso = (id: string | null, proceso: ProcesoOption | undefined) => {
    setIdProceso(id);
    if (proceso) setFechaObjetivo(proceso.periodo_hasta);
    alCambiar();
  };
  const idProcesoValido = procesoElegido ? idProceso : null;
  return { grupos, errorConexion, procesosVisibles, idGrupo, idProcesoValido, procesoElegido, fechaObjetivo,
    setFechaObjetivo, elegirGrupo, elegirProceso, solicitudActual };
}
