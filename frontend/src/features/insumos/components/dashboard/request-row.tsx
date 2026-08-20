"use client";

import { useState } from "react";
import { Check, ChevronRight, Loader2 } from "lucide-react";
import { StatusBadge, TonerBar, toneForStatusKey } from "../shared";
import { formatCountdown } from "../../hooks/use-countdown-clock";
import type { RequestRow as RequestRowType } from "../../types";
import { EMPTY_VALUE, formatArgDate } from "../../utils/format";
import { hasActiveSupply } from "./request-status";

/** Una solicitud dentro del panel expandido de un cliente (más la fila extra
 * del diagnóstico de validación, que se despliega debajo).
 *
 * La columna de acción tiene cuatro formas mutuamente excluyentes, igual que
 * el legacy: pedido ya creado (badge con el N°), pedido activo en CD, ventana
 * de validación en curso (countdown + "Cargar igual"/"Descartar"), o los
 * botones normales de carga/descarte.
 */

const CELL = "px-2 py-2 align-top";

interface RequestRowProps {
  row: RequestRowType;
  selected: boolean;
  canMutate: boolean;
  loading: boolean;
  batchRunning: boolean;
  error?: string;
  nowMs: number;
  onToggleSelect: () => void;
  onLoad: () => void;
  onDismiss: () => void;
  onValidationOverride: () => void;
  onOpenDetail: () => void;
}

export function RequestRow({
  row,
  selected,
  canMutate,
  loading,
  batchRunning,
  error,
  nowMs,
  onToggleSelect,
  onLoad,
  onDismiss,
  onValidationOverride,
  onOpenDetail,
}: RequestRowProps) {
  const [diagnosisOpen, setDiagnosisOpen] = useState(false);
  const selectable = !row.orderId && !hasActiveSupply(row) && !row.validationPending;
  const showDiagnosis = row.validationPending && diagnosisOpen && row.validationDiagnosisDetail;

  return (
    <>
      <tr className={showDiagnosis ? "" : "border-b border-border/50"}>
        <td className={CELL}>
          {selectable ? (
            <input
              type="checkbox"
              checked={selected}
              disabled={batchRunning || loading || !canMutate}
              onChange={onToggleSelect}
              aria-label={`Seleccionar solicitud ${row.requestId}`}
              className="cursor-pointer accent-brand-orange"
            />
          ) : (
            <span className="block text-center text-muted-foreground">{EMPTY_VALUE}</span>
          )}
        </td>
        <td className={`${CELL} whitespace-nowrap tabular-nums text-muted-foreground`}>
          {row.time}
        </td>
        <td className={CELL}>
          {row.store || EMPTY_VALUE}
          {row.requiereCambioSucursal && (
            <span
              title={
                row.observacionZona ||
                "Esta zona tiene una instrucción de entrega distinta a la ubicación del equipo."
              }
              className="ml-1.5 inline-flex items-center rounded-[6px] bg-[rgba(234,179,8,.15)] px-1.5 py-0.5 text-[10px] font-bold text-[#a16207] dark:text-[#facc15]"
            >
              🚚{row.sucursalEntrega ? ` → ${row.sucursalEntrega}` : ""}
            </span>
          )}
        </td>
        <td className={CELL}>
          <a
            href={row.consumableUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-brand-orange underline underline-offset-2"
          >
            {row.serial}
          </a>
          {row.isStaleOffline && (
            <span
              title={`Último contacto SDS: ${formatArgDate(row.lastContact)} (hace ${row.daysOffline ?? "?"} días). El equipo podría no estar activo en el cliente (posible bodega).`}
              className="ml-1.5 inline-flex items-center rounded-[6px] bg-[rgba(234,179,8,.15)] px-1.5 py-0.5 text-[10px] font-bold text-[#a16207] dark:text-[#facc15]"
            >
              ⚠ Offline
            </span>
          )}
        </td>
        <td className={`${CELL} max-w-[160px] truncate`} title={row.description}>
          {row.description}
        </td>
        <td className={`${CELL} font-mono text-[10px] text-muted-foreground`}>{row.sku}</td>
        <td className={CELL}>
          <div className="flex flex-col items-end gap-0.5">
            <button
              type="button"
              onClick={onOpenDetail}
              title="Ver detalle de este consumible"
              className="flex w-[104px] cursor-pointer items-center gap-1.5"
            >
              <TonerBar percent={row.percentLeft} showValue className="w-full" />
            </button>
            {row.requestedPercent !== null && row.requestedPercent !== undefined && (
              <span
                className="font-mono text-[10px] leading-none text-muted-foreground"
                title="Porcentaje inicial al momento de la solicitud"
              >
                Ini: {row.requestedPercent}%
              </span>
            )}
          </div>
        </td>
        <td className={`${CELL} text-right`}>
          <div className="flex flex-col items-end gap-0.5">
            <span className="font-mono tabular-nums">{row.daysLeft}</span>
            {row.requestedDaysLeft !== null && row.requestedDaysLeft !== undefined && (
              <span
                className="font-mono text-[10px] leading-none text-muted-foreground"
                title="Días estimados iniciales al momento de la solicitud"
              >
                Ini: {row.requestedDaysLeft}
              </span>
            )}
          </div>
        </td>
        <td className={`${CELL} text-right font-mono tabular-nums`}>
          {row.pagesLeft ?? EMPTY_VALUE}
        </td>
        <td className={CELL}>
          <div className="flex flex-col items-start gap-1">
            <StatusBadge tone={toneForStatusKey(row.statusKey)}>{row.statusLabel}</StatusBadge>
            {row.validationPending && row.validationSwapNote && (
              <span
                title={row.validationSwapNote}
                className="text-[10px] font-semibold text-[#a16207] dark:text-[#facc15]"
              >
                ⚠ cambio de insumo
              </span>
            )}
          </div>
        </td>
        <td className={CELL}>
          {row.orderId ? (
            <span className="inline-flex items-center gap-1 rounded-[6px] bg-[rgba(34,197,94,.1)] px-2 py-1 text-[10px] font-bold text-[#16a34a] dark:text-[#4ade80]">
              <Check className="h-3 w-3" aria-hidden="true" />
              {row.orderId}
            </span>
          ) : hasActiveSupply(row) ? (
            <span className="text-[10px] italic text-muted-foreground">Activo en CD</span>
          ) : row.validationPending ? (
            <div className="flex flex-col items-start gap-1">
              <span
                title={
                  row.validationDiagnosisDetail ??
                  "Llegó directo a este nivel sin bajada gradual previa — puede ser una falla de lectura del sensor."
                }
                className="inline-flex items-center gap-1.5 rounded-[20px] bg-[rgba(88,89,91,.12)] px-2 py-1 text-[10px] font-bold text-[#58595B] dark:text-[#b5b5b5]"
              >
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#58595B] dark:bg-[#b5b5b5]" />
                Validando
                <span className="font-mono tabular-nums">
                  {formatCountdown(row.validationDeadline, nowMs)}
                </span>
              </span>
              {row.validationDiagnosisDetail && (
                <button
                  type="button"
                  onClick={() => setDiagnosisOpen((open) => !open)}
                  className="inline-flex cursor-pointer items-center gap-0.5 text-[10px] font-semibold text-brand-orange"
                >
                  <ChevronRight
                    className={`h-2.5 w-2.5 transition-transform ${diagnosisOpen ? "rotate-90" : ""}`}
                    aria-hidden="true"
                  />
                  {diagnosisOpen ? "Ocultar" : "Ver"} diagnóstico
                </button>
              )}
              {canMutate && (
                <div className="flex items-center gap-1.5 whitespace-nowrap">
                  <button
                    type="button"
                    onClick={onValidationOverride}
                    className="cursor-pointer text-[11px] font-semibold text-brand-orange underline underline-offset-2"
                  >
                    Cargar igual
                  </button>
                  <span className="text-[11px] text-muted-foreground">·</span>
                  <button
                    type="button"
                    onClick={onDismiss}
                    disabled={batchRunning}
                    className="cursor-pointer text-[11px] font-semibold text-[#dc2626] underline underline-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:text-[#f87171]"
                  >
                    Descartar
                  </button>
                </div>
              )}
              {error && <p className="max-w-[130px] text-[10px] leading-tight text-[#dc2626]">{error}</p>}
            </div>
          ) : (
            <div className="flex flex-col items-start gap-1">
              {canMutate ? (
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={onLoad}
                    disabled={loading || batchRunning}
                    className="inline-flex cursor-pointer items-center gap-1 rounded-[6px] bg-brand-orange px-2 py-1 text-[10px] font-bold text-white transition-colors hover:bg-brand-orange-hover disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {loading && <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />}
                    {loading ? "Cargando…" : "Cargar"}
                  </button>
                  <button
                    type="button"
                    onClick={onDismiss}
                    disabled={loading || batchRunning}
                    className="cursor-pointer rounded-[6px] border border-[rgba(239,68,68,.35)] px-2 py-1 text-[10px] font-bold text-[#dc2626] transition-colors hover:bg-[rgba(239,68,68,.08)] disabled:cursor-not-allowed disabled:opacity-50 dark:text-[#f87171]"
                  >
                    Descartar
                  </button>
                </div>
              ) : (
                <span className="text-[10px] italic text-muted-foreground">Sin permiso</span>
              )}
              {error && <p className="max-w-[130px] text-[10px] leading-tight text-[#dc2626]">{error}</p>}
            </div>
          )}
        </td>
      </tr>

      {showDiagnosis && (
        <tr className="border-b border-border/50 bg-muted/30">
          <td colSpan={11} className="px-4 pb-2.5 pt-0">
            <div className="rounded-[8px] border border-border bg-card p-2.5">
              {row.validationDiagnosisHeadline && (
                <p className="font-body text-[11px] font-bold text-foreground">
                  {row.validationDiagnosisHeadline}
                </p>
              )}
              <p className="whitespace-pre-line font-body text-[11px] leading-relaxed text-muted-foreground">
                {row.validationDiagnosisDetail}
              </p>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
