"use client";

import { useCallback, useEffect, useState } from "react";
import { preventivosApi } from "../api/preventivos-api";
import type {
  EquipoPreventivo,
  EstadoPreventivo,
  ZonaParque,
} from "../types/preventivos";
import { useSession } from "@/services/session-provider";

export const POR_PAGINA = 50;

export function usePreventivosView() {
  const { user, modules, can } = useSession();
  const tieneModulo = modules.some((m) => m.key === "preventivos");
  const canUpdate = user.isSuperadmin || can("preventivos", "update");

  const [zonas, setZonas] = useState<ZonaParque[] | null>(null);
  const [zona, setZona] = useState<string | null>(null);
  const [rows, setRows] = useState<EquipoPreventivo[] | null>(null);
  const [total, setTotal] = useState(0);
  const [consultadoEn, setConsultadoEn] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [pagina, setPagina] = useState(1);
  const [estado, setEstado] = useState("");
  const [soloHabilitados, setSoloHabilitados] = useState(false);
  const [busqueda, setBusqueda] = useState("");
  const [busquedaAplicada, setBusquedaAplicada] = useState("");
  const [vista, setVista] = useState<"tabla" | "mapa">("tabla");

  // La búsqueda espera 350ms de inactividad antes de pegarle al backend.
  useEffect(() => {
    const timer = setTimeout(() => {
      setBusquedaAplicada(busqueda.trim());
      setPagina(1);
    }, 350);
    return () => clearTimeout(timer);
  }, [busqueda]);

  // Catálogo de zonas una sola vez; la primera queda seleccionada.
  useEffect(() => {
    if (!tieneModulo) return;
    preventivosApi
      .listZonas()
      .then((lista) => {
        setZonas(lista);
        setZona((actual) => actual ?? lista[0]?.zona ?? null);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar zonas de preventivos:", err);
        setError("No se pudo consultar el catálogo de zonas. Reintentá.");
      });
  }, [tieneModulo]);

  const load = useCallback(
    (refresh = false) => {
      if (!zona) return Promise.resolve();
      return preventivosApi
        .listEquipos({
          zona,
          estado: (estado || undefined) as EstadoPreventivo | undefined,
          habilitado: soloHabilitados ? true : undefined,
          q: busquedaAplicada || undefined,
          page: pagina,
          size: POR_PAGINA,
          refresh,
        })
        .then((page) => {
          setRows(page.items);
          setTotal(page.total);
          setConsultadoEn(page.consultado_en);
          setError(null);
        })
        .catch((err: unknown) => {
          console.error("Error al cargar preventivos:", err);
          setError("No se pudo consultar el parque. Reintentá.");
        });
    },
    [zona, estado, soloHabilitados, busquedaAplicada, pagina],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const handleRefresh = () => {
    setRefreshing(true);
    void load(true).finally(() => setRefreshing(false));
  };

  /** Toggle optimista con rollback: el backend valida permiso igual. */
  const handleToggleHabilitacion = (equipo: EquipoPreventivo) => {
    if (!canUpdate || pendingId !== null || rows === null) return;
    const previos = rows;
    const optimista = equipo.habilitacion
      ? null
      : {
          habilitado_por: user.fullName,
          habilitado_en: new Date().toISOString(),
          nota: null,
        };
    setPendingId(equipo.id_maquina);
    setRows(
      previos.map((r) =>
        r.id_maquina === equipo.id_maquina ? { ...r, habilitacion: optimista } : r,
      ),
    );
    const operacion = equipo.habilitacion
      ? preventivosApi.deshabilitar(equipo.id_maquina).then(() => null)
      : preventivosApi.habilitar(equipo.id_maquina);
    operacion
      .then((habilitacion) => {
        setRows((actuales) =>
          actuales?.map((r) =>
            r.id_maquina === equipo.id_maquina ? { ...r, habilitacion } : r,
          ) ?? actuales,
        );
      })
      .catch((err: unknown) => {
        console.error("Error al cambiar habilitación:", err);
        setRows(previos);
        setError("No se pudo guardar la habilitación. Reintentá.");
      })
      .finally(() => setPendingId(null));
  };

  const handleSelectZona = (z: string) => {
    if (z === zona) return;
    setZona(z);
    setPagina(1);
    // La zona nueva puede tener la caché fría en el backend (2-7 s):
    // vaciar la tabla dispara skeletons + modal en vez de dejar la
    // zona anterior congelada sin feedback.
    setRows(null);
  };

  const handleEstadoChange = (v: string) => {
    setEstado(v);
    setPagina(1);
  };

  const handleSoloHabilitadosChange = (v: boolean) => {
    setSoloHabilitados(v);
    setPagina(1);
  };

  return {
    tieneModulo,
    canUpdate,
    zonas,
    zona,
    rows,
    total,
    consultadoEn,
    error,
    refreshing,
    pendingId,
    pagina,
    estado,
    soloHabilitados,
    busqueda,
    busquedaAplicada,
    vista,
    setVista,
    setBusqueda,
    setPagina,
    load,
    handleRefresh,
    handleToggleHabilitacion,
    handleSelectZona,
    handleEstadoChange,
    handleSoloHabilitadosChange,
  };
}
