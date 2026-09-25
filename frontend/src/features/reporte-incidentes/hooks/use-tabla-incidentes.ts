"use client";

import { useEffect, useState } from "react";
import { reporteIncidentesApi } from "../api/reporte-incidentes-api";
import type { CampoOrden, Incidente } from "../types/reporte";
import type { EstadoDashboard } from "./use-reporte";
import { useOptionalTableSort } from "@/shared/hooks/use-optional-table-sort";

export const TAMANO_PAGINA = 50;
const DEMORA_BUSQUEDA_MS = 350;

interface Resultado {
  clave: string;
  items: Incidente[];
  total: number;
  error: string | null;
}

/** Texto de búsqueda con debounce: el input muestra lo tipeado al instante,
 * la consulta al backend espera a que se deje de tipear. */
function useBusqueda() {
  const [texto, setTexto] = useState("");
  const [consulta, setConsulta] = useState("");
  useEffect(() => {
    const handle = setTimeout(() => setConsulta(texto.trim()), DEMORA_BUSQUEDA_MS);
    return () => clearTimeout(handle);
  }, [texto]);
  return { texto, setTexto, consulta };
}

/** Filas expandidas (por id) de la página visible. */
function useExpandidas() {
  const [ids, setIds] = useState<Set<string>>(new Set());
  const alternar = (id: string) =>
    setIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  return { ids, setIds, alternar };
}

/** Tabla "Detalle de incidentes": búsqueda, orden y paginación en el servidor
 * sobre la selección filtrada. Vuelve a la página 1 si cambia la búsqueda, el
 * orden, el pedido o los filtros; recarga también cuando sube `version`. */
const SIN_DESC_PRIMERO: readonly CampoOrden[] = [];

export function useTablaIncidentes(estado: EstadoDashboard) {
  const { pedido, filtros, version } = estado;
  const busqueda = useBusqueda();
  // Como el legacy: asc → desc → vuelve al orden del reporte (más reciente primero).
  const { sort, toggleSort } = useOptionalTableSort<CampoOrden>(SIN_DESC_PRIMERO, undefined, {
    cycleToUnsorted: true,
  });
  const [page, setPage] = useState(1);
  const expandidas = useExpandidas();

  const empresaId = pedido?.empresaId ?? "";
  const periodo = pedido?.periodo ?? "";
  const meses = pedido?.meses ?? 0;
  const { sucursal, categoria, subcategoria } = filtros;
  const q = busqueda.consulta;

  // Cambió lo que se consulta (no la página): volver a la 1 y colapsar todo.
  const claveSeleccion = [empresaId, periodo, meses, sucursal, categoria, subcategoria, q, sort.key, sort.direction].join("|");
  const [seleccionPrevia, setSeleccionPrevia] = useState(claveSeleccion);
  if (seleccionPrevia !== claveSeleccion) {
    setSeleccionPrevia(claveSeleccion);
    setPage(1);
    expandidas.setIds(new Set());
  }

  const clave = `${claveSeleccion}|${page}|${version}`;
  const [resultado, setResultado] = useState<Resultado | null>(null);

  useEffect(() => {
    if (!empresaId) return;
    let activo = true;
    reporteIncidentesApi
      .listIncidentes(
        { empresaId, periodo, meses },
        { sucursal, categoria, subcategoria },
        { q, orden: sort.key, direccion: sort.direction, page, size: TAMANO_PAGINA },
      )
      .then((p) => activo && setResultado({ clave, items: p.items, total: p.total, error: null }))
      .catch((err: unknown) => {
        if (!activo) return;
        console.error("Error al cargar los incidentes del reporte:", err);
        const mensaje = err instanceof Error ? err.message : "No se pudieron cargar los incidentes.";
        setResultado((prev) => ({ clave, items: prev?.items ?? [], total: prev?.total ?? 0, error: mensaje }));
      });
    return () => {
      activo = false;
    };
  }, [clave, empresaId, periodo, meses, sucursal, categoria, subcategoria, q, sort.key, sort.direction, page]);

  const filas = resultado?.items ?? [];
  const todasExpandidas = filas.length > 0 && filas.every((f) => expandidas.ids.has(f.id));

  return {
    texto: busqueda.texto,
    setTexto: busqueda.setTexto,
    buscando: q !== "",
    sort,
    alternarOrden: toggleSort,
    page,
    setPage,
    filas,
    total: resultado?.total ?? 0,
    error: resultado?.error ?? null,
    cargando: resultado?.clave !== clave,
    expandidas: expandidas.ids,
    alternarFila: expandidas.alternar,
    todasExpandidas,
    alternarTodas: () => expandidas.setIds(todasExpandidas ? new Set() : new Set(filas.map((f) => f.id))),
  };
}

export type EstadoTabla = ReturnType<typeof useTablaIncidentes>;
