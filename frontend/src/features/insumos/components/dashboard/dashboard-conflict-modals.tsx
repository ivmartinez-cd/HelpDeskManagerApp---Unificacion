"use client";

import { useState } from "react";
import { ConfirmationModal } from "../shared";
import { EMPTY_VALUE } from "../../utils/format";
import {
  InfoGrid,
  type ModalProps,
  RequestSummary,
  SectionLabel,
  stringOrNull,
  value,
} from "./dashboard-modal-primitives";

/** Los modales de conflicto que decide el `conflictType` de `/load` más el
 * pre-chequeo client-side de "equipo en bodega". El dispatcher vive en
 * `dashboard-modals.tsx`. */

export function DuplicateOrderModal({ modal, busy, onClose, onConfirm }: ModalProps) {
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
export function AmbiguousInsumoModal({ modal, busy, onClose, onConfirm }: ModalProps) {
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

export function StaleDeviceModal({ modal, busy, onClose, onConfirm }: ModalProps) {
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
