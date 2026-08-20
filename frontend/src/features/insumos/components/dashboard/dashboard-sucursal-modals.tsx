"use client";

import { ConfirmationModal } from "../shared";
import type { RequestRow } from "../../types";
import { InfoGrid, SectionLabel } from "./dashboard-modals";

/** Los dos modales del aviso de cambio de sucursal (zonas con instrucción de entrega
 * distinta a la ubicación del equipo, ej. Arcadium Lithium — equipos en la mina,
 * entrega en Oficina Salta). Canal Directo no admite fijar la sucursal por SOAP, así
 * que ninguno de los dos bloquea nada: son recordatorios.
 *
 * Separados de `dashboard-modals.tsx` (ya señalado como deuda de tamaño en
 * ADR-020) en vez de sumarles más líneas — reusan `ConfirmationModal` y los
 * helpers `InfoGrid`/`SectionLabel` de ahí. */

export interface SucursalNoticeState {
  visible: boolean;
  orderId: string | null;
  supplyUrl: string | null;
  sucursal: string | null;
  observacion: string;
}

interface SucursalNoticeModalProps {
  state: SucursalNoticeState;
  onClose: () => void;
}

/** Se abre después de una carga individual exitosa cuando la zona tiene el aviso — el
 * pedido ya se creó, esto solo recuerda cambiar la sucursal a mano en Canal Directo. */
export function SucursalNoticeModal({ state, onClose }: SucursalNoticeModalProps) {
  if (!state.visible) return null;
  const { orderId, supplyUrl, sucursal, observacion } = state;

  return (
    <ConfirmationModal
      isOpen
      onClose={onClose}
      onConfirm={onClose}
      title="Pedido cargado — requiere cambio de sucursal"
      variant="warning"
      confirmLabel="Entendido"
      hideCancel
      widthPx={440}
      extra={
        <div className="flex flex-col gap-2.5">
          {sucursal && (
            <InfoGrid
              rows={[{ term: "Sucursal de entrega", detail: <strong>{sucursal}</strong> }]}
            />
          )}
          <blockquote className="rounded-[8px] border border-border bg-muted/50 p-3 font-body text-xs italic leading-relaxed text-muted-foreground">
            &ldquo;{observacion}&rdquo;
          </blockquote>
          {supplyUrl && (
            <a
              href={supplyUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-semibold text-brand-orange underline underline-offset-2"
            >
              Abrir pedido en Canal Directo ↗
            </a>
          )}
        </div>
      }
    >
      El pedido{orderId ? ` ${orderId}` : ""} se creó correctamente, pero esta zona tiene una
      instrucción de entrega distinta a la ubicación del equipo. Entrá al pedido en Canal Directo
      y cambiá la sucursal antes de que se despache.
    </ConfirmationModal>
  );
}

export interface BulkSucursalState {
  visible: boolean;
  excluded: RequestRow[];
  includedCount: number;
}

interface BulkSucursalExclusionModalProps {
  state: BulkSucursalState;
  onConfirm: () => void;
  onCancel: () => void;
}

/** Se abre en vez de "Cargar seleccionados" cuando alguna fila tiene el aviso — esas
 * quedan afuera del lote (se cargan de a una para no perder el aviso post-carga); el
 * resto se puede cargar de una. */
export function BulkSucursalExclusionModal({
  state,
  onConfirm,
  onCancel,
}: BulkSucursalExclusionModalProps) {
  if (!state.visible) return null;
  const { excluded, includedCount } = state;
  const total = excluded.length + includedCount;

  return (
    <ConfirmationModal
      isOpen
      onClose={onCancel}
      onConfirm={onConfirm}
      title={`${excluded.length} de ${total} pedidos quedan fuera de esta carga`}
      variant="warning"
      confirmLabel={includedCount > 0 ? `Cargar los ${includedCount} restantes` : "Cargar"}
      confirmDisabled={includedCount === 0}
      widthPx={460}
      extra={
        <div className="flex flex-col gap-1.5">
          <SectionLabel>Zonas con entrega alternativa</SectionLabel>
          <ul className="flex max-h-56 flex-col gap-1 overflow-y-auto thin-scrollbar rounded-[8px] border border-border bg-muted/40 p-2.5 font-body text-[12px] text-foreground">
            {excluded.map((row) => (
              <li key={row.requestId} title={row.observacionZona ?? ""}>
                <span className="font-mono">{row.serial}</span> — {row.store || "—"} →{" "}
                <strong>{row.sucursalEntrega || "ver observación de zona"}</strong>
              </li>
            ))}
          </ul>
        </div>
      }
    >
      Tienen una instrucción de entrega distinta a la ubicación del equipo — hay que cargarlos de
      a uno para no perder el aviso de cambio de sucursal.{" "}
      {includedCount > 0
        ? `Los otros ${includedCount} se cargan normalmente.`
        : "No queda ningún pedido para cargar en este lote."}
    </ConfirmationModal>
  );
}
