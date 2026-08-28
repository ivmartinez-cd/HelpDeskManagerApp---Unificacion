"use client";

import { ConfirmationModal } from "../shared";
import { formatCountdown, useCountdownClock } from "../../hooks/use-countdown-clock";
import type { DashboardModal } from "../../hooks/use-order-actions";
import { EMPTY_VALUE } from "../../utils/format";
import {
  AmbiguousInsumoModal,
  DuplicateOrderModal,
  StaleDeviceModal,
} from "./dashboard-conflict-modals";
import {
  InfoGrid,
  type ModalProps,
  SectionLabel,
  stringOrNull,
} from "./dashboard-modal-primitives";

export { InfoGrid, SectionLabel } from "./dashboard-modal-primitives";

/** Los 5 modales de conflicto del Dashboard, todos montados sobre el primitivo
 * `ConfirmationModal` (Patrón 6 del handoff) en vez de 5 esqueletos propios
 * como en el legacy.
 *
 * Cuál se abre lo decide el `conflictType` de la respuesta de `/load`
 * (`today_order`/`active_supply` → duplicado, `AMBIGUOUS_INSUMO` → elegir SKU,
 * `pending_validation` → ventana de validación) salvo dos: "equipo en bodega"
 * es un pre-chequeo client-side sobre `row.isStaleOffline`, y el descarte es
 * una confirmación pura de UI.
 */

function ValidationOverrideModal({ modal, busy, onClose, onConfirm }: ModalProps) {
  const nowMs = useCountdownClock(modal.kind === "validation");
  if (modal.kind !== "validation") return null;
  const { row, conflictData } = modal;
  const deadline = row.validationDeadline ?? stringOrNull(conflictData, "deadlineAt");
  const headline = row.validationDiagnosisHeadline ?? stringOrNull(conflictData, "diagnosisHeadline");
  const detail = row.validationDiagnosisDetail ?? stringOrNull(conflictData, "diagnosisDetail");

  return (
    <ConfirmationModal
      isOpen
      onClose={onClose}
      onConfirm={() => onConfirm()}
      title="Solicitud sin confirmar"
      variant="warning"
      confirmLabel={busy ? "Cargando…" : "Cargar igual"}
      loading={busy}
      widthPx={460}
      extra={
        <div className="flex flex-col gap-3.5">
          <div className="flex flex-col gap-1.5">
            <SectionLabel>Detalles de la solicitud</SectionLabel>
            <InfoGrid
              rows={[
                ...(row.customerName ? [{ term: "Cliente", detail: row.customerName }] : []),
                { term: "Serie", detail: <span className="font-mono">{row.serial}</span> },
                {
                  term: "Nivel actual",
                  detail: <strong>{row.percentLeft ?? EMPTY_VALUE}%</strong>,
                },
                {
                  term: "Vence en",
                  detail: (
                    <span className="font-mono tabular-nums">
                      {formatCountdown(deadline, nowMs)}
                    </span>
                  ),
                },
              ]}
            />
          </div>
          {detail && (
            <div className="rounded-[8px] border border-border bg-muted/50 p-3 font-body text-xs leading-relaxed">
              {headline && (
                <p className="mb-1 font-bold text-foreground">Diagnóstico automático: {headline}</p>
              )}
              <p className="whitespace-pre-line text-muted-foreground">{detail}</p>
            </div>
          )}
        </div>
      }
    >
      La solicitud de {row.serial} ({row.description}) llegó directo a {row.percentLeft ?? "—"}% sin
      bajada gradual previa — puede ser una falla de lectura del sensor. Insight todavía no terminó
      de confirmarlo automáticamente.
    </ConfirmationModal>
  );
}

function DismissConfirmationModal({ modal, busy, onClose, onConfirm }: ModalProps) {
  if (modal.kind !== "dismiss") return null;
  const { row, count, customerName, permanent } = modal;
  const isBatch = row === null;

  return (
    <ConfirmationModal
      isOpen
      onClose={onClose}
      onConfirm={() => onConfirm()}
      title={permanent ? "Ignorar solicitud permanentemente" : "Descartar solicitudes de SDS"}
      // El descarte individual mantiene la fricción del legacy (un click). El
      // descarte en lote y el ignorado permanente piden tipear: son
      // irreversibles desde esta app.
      variant={isBatch || permanent ? "destructive" : "warning"}
      confirmText={permanent ? "IGNORAR" : "DESCARTAR"}
      confirmLabel={
        busy ? (permanent ? "Ignorando…" : "Descartando…")
        : permanent ? "Confirmar ignorar"
        : "Confirmar descarte"
      }
      loading={busy}
      widthPx={440}
      extra={
        <div className="flex flex-col gap-1.5">
          <SectionLabel>
            {isBatch ? "Detalles del descarte masivo" : "Detalles de la solicitud"}
          </SectionLabel>
          {isBatch ? (
            <InfoGrid
              rows={[
                { term: "Cliente", detail: customerName },
                {
                  term: "Cantidad seleccionada",
                  detail: <strong>{count} solicitudes</strong>,
                },
              ]}
            />
          ) : (
            <InfoGrid
              rows={[
                ...(row.customerName ? [{ term: "Cliente", detail: row.customerName }] : []),
                { term: "Serie", detail: <span className="font-mono">{row.serial}</span> },
                { term: "Consumible", detail: row.description },
                { term: "SKU", detail: <span className="font-mono">{row.sku}</span> },
                { term: "Nivel restante", detail: `${row.percentLeft ?? EMPTY_VALUE}%` },
              ]}
            />
          )}
        </div>
      }
    >
      {permanent ? (
        <>
          ¿Estás seguro de que querés ignorar esta solicitud de forma <strong>permanente</strong>?
          HP SDS va a dejar de reemitirla y no se va a revertir sola — usalo cuando sabés que esta
          alerta no debería volver a aparecer (pedido ya resuelto, o un consumible que sabés que no
          hay que cargar).
        </>
      ) : (
        <>
          ¿Confirmás descartar {isBatch ? `estas ${count} solicitudes` : "esta solicitud"}? No se
          generará ningún pedido y se cancelarán las alertas en HP SDS (pasarán a estado{" "}
          <strong>DELETED</strong>).
        </>
      )}
    </ConfirmationModal>
  );
}

interface DashboardModalsProps {
  modal: DashboardModal | null;
  busy: boolean;
  onClose: () => void;
  onConfirm: (selectedInsumoId?: string) => void;
}

export function DashboardModals({ modal, busy, onClose, onConfirm }: DashboardModalsProps) {
  if (!modal) return null;
  const props = { modal, busy, onClose, onConfirm };
  switch (modal.kind) {
    case "duplicate":
      return <DuplicateOrderModal {...props} />;
    case "ambiguous":
      return <AmbiguousInsumoModal key={modal.row.requestId} {...props} />;
    case "stale":
      return <StaleDeviceModal {...props} />;
    case "validation":
      return <ValidationOverrideModal {...props} />;
    case "dismiss":
      return <DismissConfirmationModal {...props} />;
  }
}
