"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { insumosApi } from "../api/insumos-api";
import type { AuditRow } from "../types";

/** Historial de auditoría de la pantalla Historial.
 *
 * POR QUÉ UNA VENTANA Y NO PAGINACIÓN SERVIDOR PURA: `GET /api/insumos/audit`
 * pagina en SQL pero **no filtra nada** (sus únicos query params son `page` y
 * `size`). Todo lo que la pantalla necesita — separar pedidos de acciones del
 * sistema, rango de fechas, búsqueda de texto — y también las dos reglas de
 * acción por fila (que miran si más adelante hubo un CANCELLED/RELEASED para
 * la misma solicitud) se resuelven sobre las filas que el cliente tiene en la
 * mano. Con paginación servidor pura, una pestaña como "Acciones del Sistema"
 * mostraría vacío mientras el evento está en la página 3.
 *
 * Entonces: se traen bloques de 500 filas (el orden del backend es más
 * reciente primero) y se acumulan. `total` es el real del envelope `Page<T>`,
 * así que la UI puede decir honestamente cuánto falta y ofrecer "Cargar más".
 */

export const AUDIT_WINDOW_SIZE = 500;

export interface HistorialAuditState {
  /** Filas cargadas hasta ahora (bloques de `AUDIT_WINDOW_SIZE`). */
  rows: AuditRow[];
  /** Total real de eventos en la base, del envelope del backend. */
  total: number;
  loading: boolean;
  loadingMore: boolean;
  error: string | null;
  hasMore: boolean;
  reload: () => Promise<void>;
  loadMore: () => Promise<void>;
}

function messageOf(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

export function useHistorialAudit(): HistorialAuditState {
  const [rows, setRows] = useState<AuditRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Bloques ya traídos y token de la corrida en curso: si el usuario aprieta
  // "Actualizar" mientras corre un "Cargar más", la respuesta vieja no tiene
  // que pisar la nueva lista.
  const loadedPages = useRef(0);
  const runToken = useRef(0);

  const reload = useCallback(async () => {
    const token = ++runToken.current;
    setLoading(true);
    setError(null);
    try {
      const page = await insumosApi.listAudit({ page: 1, size: AUDIT_WINDOW_SIZE });
      if (token !== runToken.current) return;
      loadedPages.current = 1;
      setRows(page.items);
      setTotal(page.total);
    } catch (err) {
      if (token !== runToken.current) return;
      setError(messageOf(err, "No se pudo cargar el historial"));
    } finally {
      if (token === runToken.current) setLoading(false);
    }
  }, []);

  const loadMore = useCallback(async () => {
    const token = runToken.current;
    const nextPage = loadedPages.current + 1;
    setLoadingMore(true);
    try {
      const page = await insumosApi.listAudit({ page: nextPage, size: AUDIT_WINDOW_SIZE });
      if (token !== runToken.current) return;
      loadedPages.current = nextPage;
      setRows((prev) => [...prev, ...page.items]);
      setTotal(page.total);
    } catch (err) {
      if (token !== runToken.current) return;
      setError(messageOf(err, "No se pudieron cargar más eventos"));
    } finally {
      if (token === runToken.current) setLoadingMore(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return {
    rows,
    total,
    loading,
    loadingMore,
    error,
    hasMore: rows.length < total,
    reload,
    loadMore,
  };
}
