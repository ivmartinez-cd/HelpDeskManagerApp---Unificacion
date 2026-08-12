"use client";

import { useState } from "react";
import { AlertTriangle, ChevronDown, ChevronRight, ShieldAlert, Info } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { formatPlainDate } from "../../utils/format";
import type { MassOutageRow } from "../../types";

/** Banner de caídas de colector con 3 niveles de certeza (portado del
 * `OutageBanner` del legacy Vue). Se renderiza en la parte superior de la
 * vista cuando hay al menos un outage en la lista, colapsado en una sola
 * línea resumen — igual que el legacy — para no tapar la tabla de equipos
 * con la lista completa de outages.
 *
 * Niveles (mismo criterio que el legacy):
 *  - "confirmado": `confirmed === true` — señal real del colector (API de monitors).
 *  - "posible":    `confirmed === false && monitorOnline === true` — heurística,
 *    pero el colector ESTÁ online → puede ser un problema de red/sitio.
 *  - "aviso":      `confirmed === false && monitorOnline === false` — heurística,
 *    sin dato de estado del colector.
 */

type OutageCertainty = "confirmado" | "posible" | "aviso";

function certaintyOf(outage: MassOutageRow): OutageCertainty {
  if (outage.confirmed) return "confirmado";
  if (outage.monitorOnline) return "posible";
  return "aviso";
}

function outageSummary(outage: MassOutageRow): string {
  const certainty = certaintyOf(outage);
  const date = formatPlainDate(outage.day);
  const ratio =
    outage.fleetSize > 0 ? ` (${outage.deviceCount} de ${outage.fleetSize} equipos)` : "";

  switch (certainty) {
    case "confirmado":
      return (
        `Caída confirmada del colector "${outage.monitorName}" el ${date} ` +
        `— ${outage.customerName}${ratio}. Los equipos afectados están excluidos de la baja.`
      );
    case "posible":
      return (
        `Posible caída de colector en ${outage.customerName} el ${date}${ratio}. ` +
        `El colector "${outage.monitorName}" está online — podría ser un problema de red o sitio.`
      );
    case "aviso":
      return (
        `Salida masiva detectada en ${outage.customerName} el ${date}${ratio}. ` +
        `Estado del colector "${outage.monitorName}" desconocido.`
      );
  }
}

const certClasses: Record<
  OutageCertainty,
  { wrapper: string; icon: string; label: string; labelText: string }
> = {
  confirmado: {
    wrapper:
      "border-[rgba(239,68,68,.3)] bg-[rgba(239,68,68,.07)] text-[#991b1b] dark:text-[#fca5a5]",
    icon: "text-[#ef4444]",
    label: "bg-[rgba(239,68,68,.15)] text-[#ef4444]",
    labelText: "Confirmado",
  },
  posible: {
    wrapper:
      "border-[rgba(234,179,8,.3)] bg-[rgba(234,179,8,.08)] text-[#92400e] dark:text-[#fde047]",
    icon: "text-[#eab308]",
    label: "bg-[rgba(234,179,8,.15)] text-[#ca9a04]",
    labelText: "Posible",
  },
  aviso: {
    wrapper:
      "border-[rgba(148,163,184,.3)] bg-[rgba(148,163,184,.08)] text-muted-foreground",
    icon: "text-[#64748b]",
    label: "bg-[rgba(148,163,184,.15)] text-[#64748b]",
    labelText: "Aviso",
  },
};

const ICON_MAP: Record<OutageCertainty, typeof AlertTriangle> = {
  confirmado: ShieldAlert,
  posible: AlertTriangle,
  aviso: Info,
};

function OutageItem({ outage }: { outage: MassOutageRow }) {
  const certainty = certaintyOf(outage);
  const classes = certClasses[certainty];
  const Icon = ICON_MAP[certainty];

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-[10px] border px-4 py-3",
        classes.wrapper,
      )}
    >
      <Icon className={cn("mt-0.5 h-[18px] w-[18px] flex-none", classes.icon)} aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <span
          className={cn(
            "mb-1 inline-block rounded-full px-2 py-0.5 font-body text-[11px] font-bold uppercase tracking-wide",
            classes.label,
          )}
        >
          {classes.labelText}
        </span>
        <p className="font-body text-sm leading-[1.5]">{outageSummary(outage)}</p>
      </div>
    </div>
  );
}

interface OutageBannerProps {
  outages: MassOutageRow[];
}

export function OutageBanner({ outages }: OutageBannerProps) {
  const [open, setOpen] = useState(false);

  if (outages.length === 0) return null;

  const ChevronIcon = open ? ChevronDown : ChevronRight;

  return (
    <div className="mb-5 overflow-hidden rounded-[10px] border border-[rgba(234,179,8,.3)] bg-[rgba(234,179,8,.08)]">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full cursor-pointer items-center gap-3 px-4 py-3 text-left"
        aria-expanded={open}
      >
        <AlertTriangle className="h-[18px] w-[18px] flex-none text-[#eab308]" aria-hidden="true" />
        <p className="flex-1 font-body text-sm font-bold text-[#92400e] dark:text-[#fde047]">
          {outages.length} caída{outages.length === 1 ? "" : "s"} de colector detectadas — no se
          ofrecen para baja
        </p>
        <ChevronIcon className="h-4 w-4 flex-none text-[#92400e] dark:text-[#fde047]" aria-hidden="true" />
      </button>

      {open && (
        <div className="flex flex-col gap-2 border-t border-[rgba(234,179,8,.3)] px-4 py-3">
          {outages.map((outage) => (
            <OutageItem key={`${outage.customerId}-${outage.day}`} outage={outage} />
          ))}
        </div>
      )}
    </div>
  );
}
