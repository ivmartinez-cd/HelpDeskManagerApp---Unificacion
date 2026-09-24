"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { despachadosApi } from "../api/despachados-api";
import type { FilaDespacho, FiltrosDespachos } from "../types/despachados";

/** Tabla "Todos los despachos": filtros y paginación los resuelve el backend
 * en SQL; este hook solo traduce el estado de la pantalla a la llamada y
 * descarta respuestas viejas (token por corrida). La búsqueda llega ya
 * debounceada desde la vista. */

export interface DespachadosListadoState {
  filas: FilaDespacho[];
  total: number;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

interface Query {
  filtros: FiltrosDespachos;
  page: number;
  size: number;
}

function claveDe({ filtros, page, size }: Query): string {
  const { texto, colores, operativa, remitoDesde, remitoHasta } = filtros;
  return [texto, colores, operativa, remitoDesde, remitoHasta, page, size].join("|");
}

export function mensajeDeError(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

export function useDespachadosListado(query: Query): DespachadosListadoState {
  const [filas, setFilas] = useState<FilaDespacho[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const queryRef = useRef(query);
  const runToken = useRef(0);

  useEffect(() => {
    queryRef.current = query;
  }, [query]);

  const reload = useCallback(async () => {
    const token = ++runToken.current;
    const { filtros, page, size } = queryRef.current;
    setLoading(true);
    try {
      const pagina = await despachadosApi.listar(filtros, page, size);
      if (token !== runToken.current) return;
      setFilas(pagina.items);
      setTotal(pagina.total);
      setError(null);
    } catch (err) {
      if (token !== runToken.current) return;
      setError(mensajeDeError(err, "No se pudieron cargar los despachos"));
    } finally {
      if (token === runToken.current) setLoading(false);
    }
  }, []);

  const clave = claveDe(query);
  useEffect(() => {
    queryRef.current = query;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- carga al cambiar filtros, mismo patrón que use-historial-pending-orders
    void reload();
    // `query` se lee por ref; la clave primitiva decide cuándo recargar.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clave, reload]);

  return { filas, total, loading, error, reload };
}
