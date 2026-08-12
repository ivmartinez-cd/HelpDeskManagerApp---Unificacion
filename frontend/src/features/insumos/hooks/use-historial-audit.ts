"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { insumosApi } from "../api/insumos-api";
import { eventFilterToParam } from "../components/historial/audit-events";
import type { AuditRow, AuditTabCounts, DateRange } from "../types";

/** Historial de auditoría de la pantalla Historial (`GET /api/insumos/audit`
 * + `GET /api/insumos/audit/summary`).
 *
 * MODELO ACTUAL: el filtrado (evento, rango, búsqueda), el scope
 * (`orders`/`system`/`all`) y la paginación son enteramente del backend. Este
 * hook solo traduce el estado de filtros que vive en `HistorialView` a la
 * llamada HTTP y guarda la respuesta — no filtra, no scopea ni pagina nada en
 * el cliente. (El orden de columnas SÍ sigue siendo client-side sobre las
 * filas de la página actual, porque el backend no lo soporta — ver
 * `audit-panel.tsx` / `audit-sort.ts`, sin cambios acá.)
 *
 * Reemplaza al modelo anterior de "ventana acumulada" (`AUDIT_WINDOW_SIZE` +
 * `loadMore`/`hasMore`): esa ventana existía porque el endpoint viejo solo
 * aceptaba `page`/`size` y todo lo demás se resolvía sobre las filas ya
 * traídas — con `scope` filtrando en SQL ya no hace falta sobre-traer para
 * que "Acciones del Sistema" no aparezca vacía.
 */

export interface AuditQuery {
  scope: "orders" | "system" | "all";
  /** Valor crudo del `<select>` de eventos (incluye el combinado
   * "Anulado / liberado"); el hook lo traduce con `eventFilterToParam`. */
  eventFilter: string;
  /** Ya debounceado por quien llama al hook. */
  search: string;
  range: DateRange | null;
  page: number;
  size: number;
}

export interface HistorialAuditState {
  rows: AuditRow[];
  /** Total FILTRADO por el backend (según `scope` + filtros), no el total
   * global de la tabla. */
  total: number;
  counts: AuditTabCounts;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

const EMPTY_COUNTS: AuditTabCounts = { orders: 0, system: 0, all: 0 };

function messageOf(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

/** Clave primitiva de los 6 campos de `AuditQuery`, para el array de
 * dependencias del efecto de carga — mismo truco que `keysRef` en
 * `use-table-sort.ts`: así el efecto no depende de la identidad del objeto
 * `query` (que el caller puede recrear en cada render). */
function queryKeyOf(query: AuditQuery): string {
  const { scope, eventFilter, search, range, page, size } = query;
  return `${scope}|${eventFilter}|${search}|${range?.startDate ?? ""}|${range?.endDate ?? ""}|${page}|${size}`;
}

export function useHistorialAudit(query: AuditQuery): HistorialAuditState {
  const [rows, setRows] = useState<AuditRow[]>([]);
  const [total, setTotal] = useState(0);
  const [counts, setCounts] = useState<AuditTabCounts>(EMPTY_COUNTS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Los valores reales de `query` se leen de acá, no de las dependencias del
  // efecto (que usa `queryKeyOf`, primitivo). El ref se sincroniza en su
  // propio efecto, nunca durante el render.
  const queryRef = useRef(query);
  useEffect(() => {
    queryRef.current = query;
  }, [query]);

  // Token de la corrida en curso: si el usuario cambia de filtro (o tipea)
  // mientras una respuesta anterior sigue en vuelo, esa respuesta vieja no
  // puede pisar el estado de la más nueva.
  const runToken = useRef(0);

  const reload = useCallback(async () => {
    const token = ++runToken.current;
    const current = queryRef.current;
    setLoading(true);
    setError(null);
    try {
      const eventParam = eventFilterToParam(current.eventFilter);
      const [page, summary] = await Promise.all([
        insumosApi.listAudit({
          page: current.page,
          size: current.size,
          scope: current.scope,
          event: eventParam,
          startDate: current.range?.startDate,
          endDate: current.range?.endDate,
          search: current.search || undefined,
        }),
        insumosApi.getAuditSummary({
          event: eventParam,
          startDate: current.range?.startDate,
          endDate: current.range?.endDate,
          search: current.search || undefined,
        }),
      ]);
      if (token !== runToken.current) return;
      // No blanquear `rows` antes: recién acá, con la respuesta nueva en
      // mano, se pisa el estado — así la tabla no parpadea vacía en cada
      // tecla mientras el usuario tipea.
      setRows(page.items);
      setTotal(page.total);
      setCounts({ orders: summary.orders, system: summary.system, all: summary.total });
    } catch (err) {
      if (token !== runToken.current) return;
      setError(messageOf(err, "No se pudo cargar el historial"));
    } finally {
      if (token === runToken.current) setLoading(false);
    }
  }, []);

  const queryKey = queryKeyOf(query);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- carga inicial y en cada cambio de filtro, mismo patrón que use-admin-users
    void reload();
  }, [queryKey, reload]);

  return { rows, total, counts, loading, error, reload };
}
