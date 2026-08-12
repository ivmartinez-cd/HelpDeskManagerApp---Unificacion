"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, Check, RefreshCw } from "lucide-react";
import { useSession } from "@/services/session-provider";
import { cn } from "@/shared/utils/cn";
import { useDashboardData } from "../../hooks/use-dashboard-data";
import { useCountdownClock } from "../../hooks/use-countdown-clock";
import { useOrderActions } from "../../hooks/use-order-actions";
import { useRequestAlerts } from "../../hooks/use-request-alerts";
import { useDesktopNotifications } from "../../hooks/use-desktop-notifications";
import { useAlertNotifications } from "../../hooks/use-alert-notifications";
import type { RequestRow } from "../../types";
import { formatArgTime } from "../../utils/format";
import { AlertsSection } from "./alerts-section";
import { ConsumableDetailModal } from "./consumable-detail-modal";
import { CustomerRequestsTable } from "./customer-requests-table";
import { DashboardModals } from "./dashboard-modals";
import { DashboardTiles } from "./dashboard-tiles";

/** Dashboard de Insumos: solicitudes de HP SDS todavía no cargadas en Canal
 * Directo, agrupadas por cliente. Compone los 4 hooks del módulo (datos +
 * acciones + alertas + reloj de countdown) y arma la pantalla.
 */

interface InsumosDashboardProps {
  /** `?customerId=` del deep-link: expande ese cliente al cargar. */
  deepLinkCustomerId: number | null;
}

function LegendDot({ color }: { color: string }) {
  return (
    <span
      className="inline-block h-2 w-2 rounded-full"
      style={{ background: color }}
      aria-hidden="true"
    />
  );
}

export function InsumosDashboard({ deepLinkCustomerId }: InsumosDashboardProps) {
  // El superadmin no tiene permisos explícitos en la sesión (`permissions: []`)
  // pero puede todo — mismo criterio que el resto de las pantallas de Insumos.
  // Cargar/descartar es `create` (crea un pedido real, con costo); reconocer
  // alertas es `update` (no crea nada, solo silencia el aviso).
  const { user, can } = useSession();
  const canMutate = user.isSuperadmin || can("insumos", "create");
  const canAckAlerts = user.isSuperadmin || can("insumos", "update");

  const router = useRouter();
  const data = useDashboardData();
  const actions = useOrderActions(data);
  const alerts = useRequestAlerts();
  const desktop = useDesktopNotifications((url) => router.push(url));
  useAlertNotifications(alerts.alerts, desktop.notify);
  const [detailRow, setDetailRow] = useState<RequestRow | null>(null);

  // Un solo intervalo de 1s para toda la tabla, y solo mientras haya alguna
  // fila en validación o un modal de validación abierto.
  const countdownNeeded = useMemo(() => {
    if (actions.modal?.kind === "validation") return true;
    return Object.values(data.requestsByCustomer).some((rows) =>
      rows.some((row) => row.validationPending),
    );
  }, [data.requestsByCustomer, actions.modal]);
  const nowMs = useCountdownClock(countdownNeeded);

  const { expandCustomer } = data;
  useEffect(() => {
    if (deepLinkCustomerId !== null && deepLinkCustomerId > 0) expandCustomer(deepLinkCustomerId);
  }, [deepLinkCustomerId, expandCustomer]);

  const thresholds = data.dashboard?.thresholds;
  const hasCustomers = data.customersWithPending.length > 0;

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold text-foreground">
            Solicitudes de insumos sin cargar
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Solicitudes de HP SDS que todavía no se cargaron en Canal Directo, por cliente.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {data.lastUpdatedAt && (
            <span className="font-body text-xs text-muted-foreground">
              Actualizado {formatArgTime(data.lastUpdatedAt)}
            </span>
          )}
          <button
            type="button"
            disabled={data.loading}
            onClick={() => void data.loadDashboard()}
            className="inline-flex cursor-pointer items-center gap-2 rounded-[8px] border border-border bg-card px-3 py-1.5 font-body text-xs font-bold text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RefreshCw
              className={cn("h-3.5 w-3.5", data.loading && "animate-spin")}
              aria-hidden="true"
            />
            {data.loading ? "Actualizando…" : "Actualizar"}
          </button>
        </div>
      </div>

      {data.error && (
        <div className="flex items-center gap-3 rounded-[10px] border border-[rgba(239,68,68,.25)] bg-[rgba(239,68,68,.07)] p-3 font-body text-sm text-[#dc2626] dark:text-[#f87171]">
          <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
          {data.error}
        </div>
      )}

      <DashboardTiles dashboard={data.dashboard} loading={data.loading} />

      <AlertsSection state={alerts} canAck={canAckAlerts} />

      {hasCustomers ? (
        <CustomerRequestsTable
          data={data}
          actions={actions}
          canMutate={canMutate}
          nowMs={nowMs}
          onOpenDetail={setDetailRow}
        />
      ) : (
        !data.loading &&
        data.dashboard && (
          <div className="mx-auto my-8 flex max-w-lg flex-col items-center gap-3 rounded-[12px] border border-border bg-card p-8 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[rgba(34,197,94,.12)] text-[#16a34a]">
              <Check className="h-6 w-6" aria-hidden="true" />
            </span>
            <div>
              <h3 className="font-heading text-base font-bold text-foreground">¡Todo al día!</h3>
              <p className="mt-1 font-body text-sm text-muted-foreground">
                No hay solicitudes de insumos pendientes para ningún cliente activo en este momento.
              </p>
            </div>
          </div>
        )
      )}

      {hasCustomers && thresholds && (
        <div className="flex flex-wrap items-center gap-4 font-body text-xs text-muted-foreground">
          <span className="font-bold">Leyenda:</span>
          <span className="flex items-center gap-1.5">
            <LegendDot color="#ef4444" />
            Crítico (≤ {thresholds.critical} días)
          </span>
          <span className="flex items-center gap-1.5">
            <LegendDot color="#F7941D" />
            Urgente ({thresholds.critical + 1}–{thresholds.urgent} días)
          </span>
          <span className="flex items-center gap-1.5">
            <LegendDot color="#eab308" />
            Atención ({thresholds.urgent + 1}–{thresholds.warning} días)
          </span>
          <span className="flex items-center gap-1.5">
            <LegendDot color="#22c55e" />
            OK (más de {thresholds.warning} días)
          </span>
        </div>
      )}

      <DashboardModals
        modal={actions.modal}
        busy={actions.modalBusy}
        onClose={actions.closeModal}
        onConfirm={(selectedInsumoId) => void actions.confirmModal(selectedInsumoId)}
      />

      {/* `key` por solicitud: abrir el detalle de otra fila monta una
          instancia limpia en vez de resetear estado a mano. */}
      {detailRow && (
        <ConsumableDetailModal
          key={detailRow.requestId}
          row={detailRow}
          onClose={() => setDetailRow(null)}
        />
      )}
    </div>
  );
}
