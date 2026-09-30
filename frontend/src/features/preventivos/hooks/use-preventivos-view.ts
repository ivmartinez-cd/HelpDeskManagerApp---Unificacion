"use client";

import { useCallback, useEffect, useState } from "react";
import { preventivosApi } from "../api/preventivos-api";
import type {
  EquipoPreventivo,
  EstadoPreventivo,
  PreventivoSortKey,
  ZonaParque,
} from "../types/preventivos";
import { useSession } from "@/services/session-provider";
import { useOptionalTableSort } from "@/shared/hooks/use-optional-table-sort";

export const POR_PAGINA = 50;

/** Habilitado: el primer clic pone arriba la habilitación más reciente. */
const DESC_PRIMERO: readonly PreventivoSortKey[] = ["habilitado"];

export function usePreventivosView() {
  const { user, modules, can } = useSession();
  const tieneModulo = modules.some((m) => m.key === "preventivos");
  const canUpdate = user.isSuperadmin || can("preventivos", "update");

  const [catalogoZonas, setCatalogoZonas] = useState<ZonaParque[] | null>(null);
  const [zonas, setZonasSeleccionadas] = useState<string[]>([]);
  const [rows, setRows] = useState<EquipoPreventivo[] | null>(null);
  const [total, setTotal] = useState(0);
  const [consultadoEn, setConsultadoEn] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [pagina, setPagina] = useState(1);
  // Vacío = todos los estados.
  const [estados, setEstados] = useState<EstadoPreventivo[]>([]);
  const [soloHabilitados, setSoloHabilitados] = useState(false);
  const [busqueda, setBusqueda] = useState("");
  const [busquedaAplicada, setBusquedaAplicada] = useState("");
  const [vista, setVista] = useState<"tabla" | "mapa">("mapa");
  // Pagina en el servidor: el orden lo resuelve el backend sobre todo el
  // parque filtrado. Sin columna activa rige el orden de negocio.
  const { sort, toggleSort } = useOptionalTableSort(DESC_PRIMERO);

  // La búsqueda espera 350ms de inactividad antes de pegarle al backend.
  useEffect(() => {
    const timer = setTimeout(() => {
      setBusquedaAplicada(busqueda.trim());
      setPagina(1);
    }, 350);
    return () => clearTimeout(timer);
  }, [busqueda]);

  // Catálogo de zonas una sola vez; arranca sin ninguna zona marcada — el
  // usuario elige una o varias desde los chips, no se asume la primera.
  useEffect(() => {
    if (!tieneModulo) return;
    preventivosApi
      .listZonas()
      .then((lista) => setCatalogoZonas(lista))
      .catch((err: unknown) => {
        console.error("Error al cargar zonas de preventivos:", err);
        setError("No se pudo consultar el catálogo de zonas. Reintentá.");
      });
  }, [tieneModulo]);

  const cargarZonas = useCallback(() => {
    setError(null);
    preventivosApi
      .listZonas()
      .then((lista) => setCatalogoZonas(lista))
      .catch((err: unknown) => {
        console.error("Error al cargar zonas de preventivos:", err);
        setError("No se pudo consultar el catálogo de zonas. Reintentá.");
      });
  }, []);

  const load = useCallback(
    (refresh = false) => {
      if (zonas.length === 0) return Promise.resolve();
      return preventivosApi
        .listEquipos({
          zonas,
          estados,
          habilitado: soloHabilitados ? true : undefined,
          q: busquedaAplicada || undefined,
          page: pagina,
          size: POR_PAGINA,
          refresh,
          sortBy: sort.key ?? undefined,
          sortDir: sort.direction,
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
    [zonas, estados, soloHabilitados, busquedaAplicada, pagina, sort],
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

  /** Clic en un chip de zona: la agrega o la saca de la selección. */
  const handleToggleZona = (z: string) => {
    setZonasSeleccionadas((actuales) =>
      actuales.includes(z) ? actuales.filter((x) => x !== z) : [...actuales, z],
    );
    setPagina(1);
    // La zona nueva puede tener la caché fría en el backend (2-7 s):
    // vaciar la tabla dispara skeletons + modal en vez de dejar la
    // selección anterior congelada sin feedback.
    setRows(null);
  };

  const handleEstadosChange = (v: EstadoPreventivo[]) => {
    setEstados(v);
    setPagina(1);
  };

  const handleSoloHabilitadosChange = (v: boolean) => {
    setSoloHabilitados(v);
    setPagina(1);
  };

  const ordenarPor = (key: PreventivoSortKey) => {
    toggleSort(key);
    setPagina(1);
  };

  return {
    tieneModulo,
    canUpdate,
    catalogoZonas,
    zonas,
    rows,
    total,
    consultadoEn,
    error,
    refreshing,
    pendingId,
    pagina,
    estados,
    soloHabilitados,
    busqueda,
    busquedaAplicada,
    vista,
    setVista,
    setBusqueda,
    setPagina,
    load,
    cargarZonas,
    handleRefresh,
    handleToggleHabilitacion,
    handleToggleZona,
    handleEstadosChange,
    handleSoloHabilitadosChange,
    sort,
    ordenarPor,
  };
}
