"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";
import { insumosApi } from "../api/insumos-api";
import type { AuditRow } from "../types";

/** Las dos acciones condicionales del Historial: anular un pedido vivo y
 * vincular ("reconciliar") uno huérfano.
 *
 * TRAMPA DEL BACKEND: `/cancel` y `/reconcile` responden **200 aunque
 * fallen** — el error de negocio viaja en el body (`ok:false` + `error`), no
 * como status HTTP. Por eso se ramifica por `response.ok` y el `catch` queda
 * para errores de red/permisos reales.
 *
 * El modal de confirmación no se cierra si la operación falla: el error se
 * muestra adentro para que el operador vea qué pasó sin perder el contexto.
 */

export type AuditActionKind = "cancel" | "reconcile";

export interface PendingAuditAction {
  row: AuditRow;
  kind: AuditActionKind;
}

export interface HistorialAuditActionsState {
  pending: PendingAuditAction | null;
  busyRequestId: number | null;
  error: string | null;
  running: boolean;
  ask: (row: AuditRow, kind: AuditActionKind) => void;
  dismiss: () => void;
  confirm: () => Promise<void>;
}

export function useHistorialAuditActions(
  onSuccess: () => Promise<void> | void,
): HistorialAuditActionsState {
  const [pending, setPending] = useState<PendingAuditAction | null>(null);
  const [busyRequestId, setBusyRequestId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const ask = useCallback((row: AuditRow, kind: AuditActionKind) => {
    setError(null);
    setPending({ row, kind });
  }, []);

  const dismiss = useCallback(() => {
    setPending(null);
    setError(null);
  }, []);

  const confirm = useCallback(async () => {
    if (!pending) return;
    const { row, kind } = pending;
    const requestId = row.hp_request_id;
    if (!requestId) return;

    setBusyRequestId(requestId);
    setError(null);
    try {
      if (kind === "cancel") {
        const response = await insumosApi.cancelRequest(requestId);
        if (!response.ok) {
          const message = response.error ?? "No se pudo anular el pedido";
          setError(message);
          toast.error(message);
          return;
        }
        toast.success(`Pedido ${row.internal_order_id ?? requestId} anulado`);
      } else {
        if (!row.customer_id) return;
        const response = await insumosApi.reconcileRequest(requestId, {
          customerId: row.customer_id,
          customerName: row.customer_name ?? "",
        });
        if (!response.ok) {
          const message = response.error ?? "No se encontró ningún pedido para vincular";
          setError(message);
          toast.error(message);
          return;
        }
        toast.success(
          response.alreadyLinked
            ? `El pedido ${response.orderId ?? ""} ya estaba vinculado`.trim()
            : `Pedido ${response.orderId ?? ""} vinculado`.trim(),
        );
      }
      setPending(null);
      await onSuccess();
    } catch (err) {
      const message =
        err instanceof Error && err.message ? err.message : "La operación falló";
      setError(message);
      toast.error(message);
    } finally {
      setBusyRequestId(null);
    }
  }, [pending, onSuccess]);

  return {
    pending,
    busyRequestId,
    error,
    running: busyRequestId !== null,
    ask,
    dismiss,
    confirm,
  };
}
