"use client";

import { useState } from "react";
import { Bell, ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import type { AlertSeverity, ClassifiedAlert, RequestAlertsState } from "../../hooks/use-request-alerts";
import { formatArgDateTime } from "../../utils/format";

/** Sección colapsable de alertas escaladas (Patrón 3 del handoff): 3 niveles
 * de severidad, crítico siempre expandido y los otros dos con chevron.
 *
 * El backend no manda severidad — se deriva de la antigüedad de la solicitud;
 * ver el mapeo documentado en `hooks/use-request-alerts.ts`.
 */

interface LevelStyle {
  border: string;
  headerBg: string;
  dot: string;
  title: string;
  label: string;
  emoji: string;
}

const LEVEL_STYLES: Record<AlertSeverity, LevelStyle> = {
  critical: {
    border: "border-[1.5px] border-[#ef4444]",
    headerBg: "bg-[rgba(239,68,68,.08)]",
    dot: "bg-[#ef4444]",
    title: "text-[#dc2626] dark:text-[#f87171]",
    label: "Crítico",
    emoji: "🔴",
  },
  warning: {
    border: "border-[1.5px] border-[#eab308]",
    headerBg: "bg-[rgba(234,179,8,.07)]",
    dot: "bg-[#eab308]",
    title: "text-[#a16207] dark:text-[#facc15]",
    label: "Advertencia",
    emoji: "🟡",
  },
  info: {
    border: "border-[1.5px] border-border",
    headerBg: "bg-card",
    dot: "bg-[#58595B]",
    title: "text-[#58595B] dark:text-[#b5b5b5]",
    label: "Informativo",
    emoji: "ℹ️",
  },
};

const LEVEL_DESCRIPTIONS: Record<AlertSeverity, string> = {
  critical: "esperando hace más de 24 h",
  warning: "esperando hace más de 8 h",
  info: "escaladas recientemente",
};

function formatAge(hours: number): string {
  if (hours >= 48) return `hace ${Math.floor(hours / 24)} días`;
  if (hours >= 1) return `hace ${Math.floor(hours)} h`;
  return `hace ${Math.max(1, Math.round(hours * 60))} min`;
}

function AlertRowItem({
  alert,
  canAck,
  onAck,
}: {
  alert: ClassifiedAlert;
  canAck: boolean;
  onAck: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2.5 rounded-[8px] bg-muted/50 px-3 py-2">
      <span className="flex-1 font-body text-[13px] text-foreground">
        <strong>{alert.customerName}</strong> · <span className="font-mono">{alert.deviceSerial}</span>{" "}
        · {alert.description}
      </span>
      <span
        className="font-body text-[11px] text-muted-foreground"
        title={`Solicitado: ${formatArgDateTime(alert.requestedAt ?? alert.firstSeenAt)}`}
      >
        {formatAge(alert.ageHours)}
      </span>
      {canAck && (
        <button
          type="button"
          onClick={onAck}
          className="rounded-[6px] border border-border px-2.5 py-1 font-body text-[11px] font-bold text-foreground transition-colors hover:bg-muted"
        >
          Reconocer
        </button>
      )}
    </div>
  );
}

function SeverityGroup({
  severity,
  alerts,
  canAck,
  onAck,
}: {
  severity: AlertSeverity;
  alerts: ClassifiedAlert[];
  canAck: boolean;
  onAck: (ids: number[]) => void;
}) {
  // El nivel crítico va siempre expandido y no es colapsable (regla del
  // Patrón 3); los otros dos arrancan cerrados.
  const [open, setOpen] = useState(false);
  const style = LEVEL_STYLES[severity];
  const collapsible = severity !== "critical";
  const expanded = !collapsible || open;

  if (alerts.length === 0) return null;

  return (
    <div className={cn("overflow-hidden rounded-[10px]", style.border)}>
      <div
        className={cn(
          "flex items-center gap-3 px-4 py-3",
          style.headerBg,
          collapsible && "cursor-pointer",
        )}
        onClick={collapsible ? () => setOpen((value) => !value) : undefined}
      >
        <span className={cn("h-2 w-2 flex-none rounded-full", style.dot)} aria-hidden="true" />
        <span className={cn("flex-1 font-heading text-sm font-bold", style.title)}>
          {style.emoji} {style.label} — {alerts.length} solicitud(es) sin cargar
        </span>
        <span className="font-body text-xs text-muted-foreground">
          {LEVEL_DESCRIPTIONS[severity]}
        </span>
        {canAck && (
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              onAck(alerts.map((alert) => alert.hpRequestId));
            }}
            className={cn(
              "rounded-[6px] border bg-card px-3 py-1 font-body text-xs font-bold transition-colors hover:bg-muted",
              severity === "critical" ? "border-[#ef4444] text-[#dc2626]" : "border-border text-foreground",
            )}
          >
            Reconocer todas
          </button>
        )}
        {collapsible && (
          <ChevronDown
            className={cn(
              "h-3.5 w-3.5 text-muted-foreground transition-transform",
              expanded && "rotate-180",
            )}
            aria-hidden="true"
          />
        )}
      </div>
      {expanded && (
        <div className="flex flex-col gap-1.5 border-t border-border bg-card px-4 py-3">
          {alerts.map((alert) => (
            <AlertRowItem
              key={alert.hpRequestId}
              alert={alert}
              canAck={canAck}
              onAck={() => onAck([alert.hpRequestId])}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface AlertsSectionProps {
  state: RequestAlertsState;
  canAck: boolean;
}

export function AlertsSection({ state, canAck }: AlertsSectionProps) {
  const [open, setOpen] = useState(true);
  if (state.loading || state.alerts.length === 0) return null;

  const acknowledge = (ids: number[]) => void state.acknowledge(ids);

  return (
    <section className="flex flex-col gap-2.5">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex items-center gap-2 self-start font-heading text-sm font-bold text-foreground"
      >
        <ChevronRight
          className={cn("h-4 w-4 transition-transform", open && "rotate-90")}
          aria-hidden="true"
        />
        <Bell className="h-4 w-4 text-[#dc2626]" aria-hidden="true" />
        Alertas escaladas
        <span className="rounded-[20px] bg-[rgba(239,68,68,.1)] px-2 py-0.5 font-body text-[11px] font-bold text-[#dc2626] dark:text-[#f87171]">
          {state.total}
        </span>
      </button>

      {open && (
        <div className="flex flex-col gap-2.5">
          {(["critical", "warning", "info"] as const).map((severity) => (
            <SeverityGroup
              key={severity}
              severity={severity}
              alerts={state.bySeverity[severity]}
              canAck={canAck && !state.acknowledging}
              onAck={acknowledge}
            />
          ))}
        </div>
      )}
    </section>
  );
}
