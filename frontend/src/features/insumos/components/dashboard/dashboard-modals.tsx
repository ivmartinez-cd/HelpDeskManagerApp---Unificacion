"use client";

import { useState, type ReactNode } from "react";
import { ConfirmationModal } from "../shared";
import { formatCountdown, useCountdownClock } from "../../hooks/use-countdown-clock";
import type { DashboardModal } from "../../hooks/use-order-actions";
import type { RequestRow } from "../../types";
import { EMPTY_VALUE } from "../../utils/format";

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

function value(data: Record<string, unknown> | null | undefined, key: string): string {
  const raw = data?.[key];
  if (raw === null || raw === undefined || raw === "") return EMPTY_VALUE;
  return String(raw);
}

function stringOrNull(data: Record<string, unknown> | null | undefined, key: string): string | null {
  const raw = data?.[key];
  return typeof raw === "string" && raw.length > 0 ? raw : null;
}

/** Grilla `término / valor` de dos columnas, el mismo `<dl>` de los modales
 * del legacy. Las filas son objetos y no tuplas para no meter JSX suelto
 * dentro de un array literal (regla `react/jsx-key`). */
interface InfoRow {
  term: string;
  detail: ReactNode;
}

export function InfoGrid({ rows }: { rows: InfoRow[] }) {
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 font-body text-[13px]">
      {rows.map((row, index) => (
        <div key={`${row.term}-${index}`} className="contents">
          <dt className="whitespace-nowrap text-muted-foreground">{row.term}</dt>
          <dd className="break-all text-foreground">{row.detail}</dd>
        </div>
      ))}
    </dl>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h3 className="font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground">
      {children}
    </h3>
  );
}

function RequestSummary({ row }: { row: RequestRow }) {
  return (
    <div className="flex flex-col gap-1.5">
      <SectionLabel>Solicitud</SectionLabel>
      <InfoGrid
        rows={[
          ...(row.customerName ? [{ term: "Cliente", detail: row.customerName }] : []),
          { term: "Serie", detail: <span className="font-mono">{row.serial}</span> },
          { term: "Consumible", detail: row.description },
          { term: "SKU", detail: <span className="font-mono">{row.sku}</span> },
        ]}
      />
    </div>
  );
}

interface ModalProps {
  modal: DashboardModal;
  busy: boolean;
  onClose: () => void;
  onConfirm: (selectedInsumoId?: string) => void;
}

function DuplicateOrderModal({ modal, busy, onClose, onConfirm }: ModalProps) {
  if (modal.kind !== "duplicate") return null;
  const isToday = modal.conflictType === "today_order";
  const supplyUrl = stringOrNull(modal.conflictData, "supplyUrl");
  const orderLabel = isToday
    ? value(modal.conflictData, "orderId")
    : value(modal.conflictData, "supplyId");

  return (
    <ConfirmationModal
      isOpen
      onClose={onClose}
      onConfirm={() => onConfirm()}
      title="Pedido duplicado detectado"
      variant="warning"
      confirmLabel={busy ? "Cargando…" : "Cargar igual"}
      loading={busy}
      widthPx={460}
      extra={
        <div className="flex flex-col gap-3.5">
          <RequestSummary row={modal.row} />
          <div className="h-px bg-border" />
          <div className="flex flex-col gap-1.5">
            <SectionLabel>
              {isToday ? "Pedido cargado hoy" : "Pedido activo en Canal Directo"}
            </SectionLabel>
            <InfoGrid
              rows={[
                {
                  term: "N° pedido",
                  detail: supplyUrl ? (
                    <a
                      href={supplyUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-mono text-brand-orange underline underline-offset-2"
                    >
                      {orderLabel} ↗
                    </a>
                  ) : (
                    <span className="font-mono">{orderLabel}</span>
                  ),
                },
                ...(isToday
                  ? [
                      {
                        term: "SKU",
                        detail: (
                          <span className="font-mono">{value(modal.conflictData, "sku")}</span>
                        ),
                      },
                      { term: "Cargado a las", detail: value(modal.conflictData, "createdAt") },
                    ]
                  : [
                      { term: "Estado en CD", detail: value(modal.conflictData, "estado") },
                      { term: "Fecha del pedido", detail: value(modal.conflictData, "fecha") },
                    ]),
              ]}
            />
          </div>
        </div>
      }
    >
      Si cargás igual, se creará un <strong>pedido adicional</strong> para esta serie aunque ya
      exista uno. Verificá en Canal Directo antes de confirmar.
    </ConfirmationModal>
  );
}

/** Se monta con `key` por solicitud desde el dispatcher, así que el estado
 * arranca limpio en cada apertura sin resincronizar nada en un efecto. */
function AmbiguousInsumoModal({ modal, busy, onClose, onConfirm }: ModalProps) {
  const firstId = modal.kind === "ambiguous" ? (modal.options[0]?.id ?? null) : null;
  const [selectedId, setSelectedId] = useState<string | null>(firstId);

  if (modal.kind !== "ambiguous") return null;

  return (
    <ConfirmationModal
      isOpen
      onClose={onClose}
      onConfirm={() => selectedId && onConfirm(selectedId)}
      title="Insumo ambiguo"
      variant="simple"
      confirmLabel={busy ? "Cargando…" : "Confirmar selección"}
      loading={busy}
      widthPx={460}
      extra={
        <div className="flex flex-col gap-3.5">
          <RequestSummary row={modal.row} />
          <div className="flex flex-col gap-1.5">
            <SectionLabel>Elegí el insumo correcto</SectionLabel>
            <div className="flex max-h-56 flex-col gap-1.5 overflow-y-auto thin-scrollbar">
              {modal.options.map((option) => (
                <label
                  key={option.id}
                  className="flex cursor-pointer items-center gap-2.5 rounded-[8px] border border-border px-2.5 py-2 transition-colors hover:border-brand-orange hover:bg-brand-orange/5"
                >
                  <input
                    type="radio"
                    name="insumo-option"
                    value={option.id}
                    checked={selectedId === option.id}
                    onChange={() => setSelectedId(option.id)}
                    className="accent-brand-orange"
                  />
                  <span className="font-body text-[13px] text-foreground">{option.name}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      }
    >
      El sistema no pudo determinar automáticamente cuál insumo corresponde. Verificá la capacidad o
      variante antes de confirmar.
    </ConfirmationModal>
  );
}

function StaleDeviceModal({ modal, busy, onClose, onConfirm }: ModalProps) {
  if (modal.kind !== "stale") return null;
  const { row } = modal;
  return (
    <ConfirmationModal
      isOpen
      onClose={onClose}
      onConfirm={() => onConfirm()}
      title="Equipo posiblemente en bodega"
      variant="warning"
      confirmLabel={busy ? "Cargando…" : "Cargar igual"}
      loading={busy}
      widthPx={440}
      extra={
        <div className="flex flex-col gap-1.5">
          <SectionLabel>Detalles del equipo</SectionLabel>
          <InfoGrid
            rows={[
              ...(row.customerName ? [{ term: "Cliente", detail: row.customerName }] : []),
              { term: "Serie", detail: <span className="font-mono">{row.serial}</span> },
              {
                term: "Días sin contacto",
                detail: <strong>{row.daysOffline ?? EMPTY_VALUE}</strong>,
              },
            ]}
          />
        </div>
      }
    >
      El equipo {row.serial} lleva {row.daysOffline ?? "varios"} días sin conexión con SDS y podría
      estar en bodega. ¿Querés intentar la carga igual?
    </ConfirmationModal>
  );
}

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
  const { row, count, customerName } = modal;
  const isBatch = row === null;

  return (
    <ConfirmationModal
      isOpen
      onClose={onClose}
      onConfirm={() => onConfirm()}
      title="Descartar solicitudes de SDS"
      // El descarte individual mantiene la fricción del legacy (un click). El
      // descarte en lote pide tipear: borra N solicitudes en HP SDS de una y
      // no hay forma de revertirlo desde esta app.
      variant={isBatch ? "destructive" : "warning"}
      confirmText="DESCARTAR"
      confirmLabel={busy ? "Descartando…" : "Confirmar descarte"}
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
      ¿Confirmás descartar {isBatch ? `estas ${count} solicitudes` : "esta solicitud"}? No se
      generará ningún pedido y se cancelarán las alertas en HP SDS (pasarán a estado{" "}
      <strong>DELETED</strong>).
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
