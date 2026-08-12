"use client";

import { useCallback, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { useSession } from "@/services/session-provider";
import type { DateRange } from "../../types";
import { formatArgTime } from "../../utils/format";
import { useDebouncedValue } from "../../hooks/use-debounced-value";
import { useHistorialAudit, type AuditQuery } from "../../hooks/use-historial-audit";
import { useHistorialMailLog } from "../../hooks/use-historial-mail-log";
import { useHistorialPendingOrders } from "../../hooks/use-historial-pending-orders";
import { EVENT_FILTER_ALL } from "./audit-events";
import { AuditPanel } from "./audit-panel";
import { HistorialFilters } from "./historial-filters";
import { MailLogPanel } from "./mail-log-panel";
import { PendingOrdersTable } from "./pending-orders-table";
import {
  DEFAULT_TAB,
  HistorialTabs,
  isAuditTab,
  isHistorialTab,
  type HistorialTab,
} from "./historial-tabs";

/** Pantalla `/insumos/historial`: 5 pestañas sobre 3 fuentes de datos
 * (`/audit`, `/orders/pending`, `/mail-log`).
 *
 * - La pestaña activa vive en `?tab=` y se escribe con `router.replace` (no
 *   `push`): cambiar de pestaña no es navegación, no tiene que ensuciar el
 *   botón "atrás" del navegador.
 * - El historial de auditoría se pide siempre (con `scope="all"` fuera de sus
 *   tres pestañas), porque `audit.counts` alimenta los contadores de las tres
 *   pestañas de auditoría sin importar cuál está a la vista. El log de mails
 *   es lazy y los pedidos pendientes (el endpoint más caro) solo se piden y
 *   se pollean con su pestaña a la vista.
 * - Esta pantalla es la dueña de todo el estado de filtros de auditoría
 *   (`eventFilter`, `page`, `size`, más `search`/`range` que ya tenía) y arma
 *   el `AuditQuery` para `useHistorialAudit` — `AuditPanel` es un consumidor,
 *   no un dueño, de ese estado.
 */

const PENDING_STATUS = "Pendiente";
const PAGE_SIZES = [25, 50, 100] as const;

export function HistorialView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, can } = useSession();

  const tabParam = searchParams.get("tab");
  const tab: HistorialTab = isHistorialTab(tabParam) ? tabParam : DEFAULT_TAB;

  // Deep-link del Dashboard/notificaciones: abre ese cliente ya expandido.
  const customerIdParam = Number(searchParams.get("customerId"));
  const initialExpandedCustomerId =
    Number.isFinite(customerIdParam) && customerIdParam > 0 ? customerIdParam : null;

  const [search, setSearch] = useState("");
  const [range, setRange] = useState<DateRange | null>(null);
  const [includeDelivered, setIncludeDelivered] = useState(false);

  // Estado de filtros de la tabla de auditoría (pestañas Solo Pedidos /
  // Acciones del Sistema / Todos): `search`/`range` son compartidos con la
  // pestaña Pendientes, pero `eventFilter`/`page`/`size` son propios de acá.
  const [eventFilter, setEventFilter] = useState(EVENT_FILTER_ALL);
  const [page, setPage] = useState(1);
  const [size, setSize] = useState<number>(PAGE_SIZES[0]);

  // La búsqueda que llega al backend va debounceada — el input (`search`) se
  // actualiza en cada tecla para que se sienta inmediato, pero el fetch se
  // retrasa 350ms. Solo aplica a la tabla de auditoría: Pendientes y Mails
  // siguen filtrando client-side sobre `search` crudo.
  const debouncedSearch = useDebouncedValue(search, 350);

  // Scope del audit fetch: el tab activo si es una de las tres pestañas de
  // auditoría, o "all" en cualquier otra (Pendientes/Mails) — así
  // `audit.counts` sigue alimentando los tres badges aunque ninguna esté a
  // la vista.
  const auditScope: AuditQuery["scope"] = isAuditTab(tab)
    ? (tab as AuditQuery["scope"])
    : "all";

  // Volver a página 1 cuando cambia cualquier filtro que afecte qué trae el
  // backend (ajuste de estado durante el render, no un efecto). El orden de
  // columnas queda afuera a propósito: es client-side sobre la página ya
  // traída, cambiarlo no cambia qué página pedir.
  const auditFilterKey = `${auditScope}/${eventFilter}/${debouncedSearch}/${range?.startDate ?? ""}-${range?.endDate ?? ""}/${size}`;
  const [prevAuditFilterKey, setPrevAuditFilterKey] = useState(auditFilterKey);
  if (auditFilterKey !== prevAuditFilterKey) {
    setPrevAuditFilterKey(auditFilterKey);
    setPage(1);
  }

  const audit = useHistorialAudit({
    scope: auditScope,
    eventFilter,
    search: debouncedSearch,
    range,
    page,
    size,
  });
  const pending = useHistorialPendingOrders({ active: tab === "pendientes", includeDelivered });
  const mailLog = useHistorialMailLog(tab === "mails");

  // `can()` solo refleja grants explícitos; un superadmin ve el módulo sin
  // tenerlos. Las dos acciones pegan a `/cancel` y `/reconcile`, que del lado
  // del backend exigen `insumos:create` (no `update`): ese es el gate.
  const canAct = user.isSuperadmin || can("insumos", "create");

  const setTab = useCallback(
    (next: HistorialTab) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set("tab", next);
      router.replace(`/insumos/historial?${params.toString()}`, { scroll: false });
    },
    [router, searchParams],
  );

  const counts = useMemo(
    () => ({
      pendientes: pending.orders.filter((order) => order.supplyStatus === PENDING_STATUS).length,
      orders: audit.counts.orders,
      system: audit.counts.system,
      all: audit.counts.all,
      mails: mailLog.loaded ? mailLog.total : null,
    }),
    [pending.orders, audit.counts, mailLog.loaded, mailLog.total],
  );

  const refreshing =
    tab === "pendientes" ? pending.loading : tab === "mails" ? mailLog.loading : audit.loading;

  const refresh = useCallback(() => {
    if (tab === "pendientes") return void pending.refresh();
    if (tab === "mails") return void mailLog.reload();
    return void audit.reload();
  }, [tab, pending, mailLog, audit]);

  const error =
    tab === "pendientes" ? pending.error : tab === "mails" ? mailLog.error : audit.error;

  return (
    <div className="flex flex-col gap-5 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold text-foreground">
            Historial de pedidos y auditoría
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Registro auditado de pedidos de insumos cargados, fallos y acciones automáticas de la
            app.
          </p>
        </div>
        <button
          type="button"
          onClick={refresh}
          disabled={refreshing}
          className="inline-flex cursor-pointer items-center gap-2 rounded-[8px] border border-border bg-card px-3.5 py-2.5 font-body text-sm font-semibold text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:pointer-events-none disabled:opacity-50"
        >
          <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} aria-hidden="true" />
          Actualizar
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-2.5 rounded-[10px] border border-[rgba(239,68,68,.25)] bg-[rgba(239,68,68,.07)] p-3.5 font-body text-[13px] text-[#991b1b] dark:text-[#fca5a5]">
          <AlertTriangle className="h-4 w-4 flex-none" aria-hidden="true" />
          {error}
        </div>
      )}

      <HistorialTabs value={tab} onChange={setTab} counts={counts} />

      {tab === "pendientes" && (
        <div className="flex flex-col gap-4">
          <HistorialFilters
            search={search}
            onSearchChange={setSearch}
            searchPlaceholder="Buscar cliente, sucursal, serie, SKU…"
            range={range}
            onRangeChange={setRange}
            summary={
              pending.lastUpdated ? (
                <>Actualizado {formatArgTime(pending.lastUpdated.toISOString())} · refresco cada 90s</>
              ) : null
            }
          >
            <label className="flex items-center gap-2 font-body text-xs text-muted-foreground">
              <input
                type="checkbox"
                checked={includeDelivered}
                onChange={(event) => setIncludeDelivered(event.target.checked)}
                className="h-3.5 w-3.5 accent-[#F7941D]"
              />
              Incluir entregados
            </label>
          </HistorialFilters>

          <PendingOrdersTable
            orders={pending.orders}
            loading={pending.loading}
            search={search}
            range={range}
            initialExpandedCustomerId={initialExpandedCustomerId}
          />
        </div>
      )}

      {isAuditTab(tab) && (
        <AuditPanel
          audit={audit}
          eventFilter={eventFilter}
          onEventFilterChange={setEventFilter}
          search={search}
          onSearchChange={setSearch}
          range={range}
          onRangeChange={setRange}
          page={page}
          onPageChange={setPage}
          size={size}
          onSizeChange={setSize}
          sizes={PAGE_SIZES}
          canAct={canAct}
        />
      )}

      {tab === "mails" && (
        <MailLogPanel
          mailLog={mailLog}
          search={search}
          onSearchChange={setSearch}
          range={range}
          onRangeChange={setRange}
        />
      )}
    </div>
  );
}
