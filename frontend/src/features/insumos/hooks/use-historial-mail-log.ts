"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { insumosApi } from "../api/insumos-api";
import type { MailLogRow } from "../types";

/** Log de mails salientes (pestaña "Mails enviados").
 *
 * Carga LAZY: no se pide nada hasta que el usuario entra a la pestaña por
 * primera vez (`active`), y una vez cargada una página no se vuelve a pedir al
 * ir y volver de pestaña — solo al cambiar de página/tamaño o al apretar
 * "Actualizar".
 *
 * Acá sí se usa la paginación real del servidor (`page`/`size` del envelope
 * `Page<T>`): a diferencia del historial de auditoría, ninguna regla de esta
 * tabla necesita mirar filas de otras páginas. La búsqueda y el filtro por
 * tipo siguen siendo client-side sobre la página cargada, porque el endpoint
 * no acepta ningún otro query param.
 */

export const MAIL_LOG_PAGE_SIZES = [25, 50, 100] as const;

export interface HistorialMailLogState {
  rows: MailLogRow[];
  total: number;
  page: number;
  size: number;
  loading: boolean;
  error: string | null;
  /** Ya se trajo al menos una página (para no mostrar "vacío" antes de pedir). */
  loaded: boolean;
  setPage: (page: number) => void;
  setSize: (size: number) => void;
  reload: () => Promise<void>;
}

export function useHistorialMailLog(active: boolean): HistorialMailLogState {
  const [rows, setRows] = useState<MailLogRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [size, setSizeState] = useState<number>(MAIL_LOG_PAGE_SIZES[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const fetchedKey = useRef<string | null>(null);
  const runToken = useRef(0);

  const load = useCallback(async () => {
    const key = `${page}/${size}`;
    const token = ++runToken.current;
    fetchedKey.current = key;
    setLoading(true);
    setError(null);
    try {
      const result = await insumosApi.listMailLog({ page, size });
      if (token !== runToken.current) return;
      setRows(result.items);
      setTotal(result.total);
      setLoaded(true);
    } catch (err) {
      if (token !== runToken.current) return;
      // Se limpia la marca para que un reintento (o volver a la pestaña)
      // vuelva a pedir en vez de quedarse pegado con el error.
      fetchedKey.current = null;
      setError(err instanceof Error && err.message ? err.message : "No se pudo cargar el log de mails");
    } finally {
      if (token === runToken.current) setLoading(false);
    }
  }, [page, size]);

  useEffect(() => {
    if (!active) return;
    if (fetchedKey.current === `${page}/${size}`) return;
    void load();
  }, [active, load, page, size]);

  const setSize = useCallback((next: number) => {
    setSizeState(next);
    setPage(1);
  }, []);

  const reload = useCallback(() => {
    fetchedKey.current = null;
    return load();
  }, [load]);

  return { rows, total, page, size, loading, error, loaded, setPage, setSize, reload };
}
