"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight, ExternalLink, Route } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import type { Alerta, Incidente } from "../types/liquidaciones";
import { formatARS, formatFecha } from "../lib/format";
import { incidentUrl } from "@/shared/utils/incident-link";

function computeRutasCompartidas(incidentes: Incidente[]): Set<string> {
  const ids = new Set<string>();
  const byFecha = new Map<string, Incidente[]>();
  for (const inc of incidentes) {
    if (!inc.fechaCierre || (inc.cantKmCobrado ?? 0) <= 0) continue;
    const list = byFecha.get(inc.fechaCierre) ?? [];
    list.push(inc);
    byFecha.set(inc.fechaCierre, list);
  }
  for (const incsDay of byFecha.values()) {
    if (incsDay.length < 2) continue;
    for (const inc of incsDay) {
      for (const otro of incsDay) {
        if (otro.id === inc.id) continue;
        const mismaLocalidad =
          inc.localidadCliente &&
          otro.localidadCliente &&
          inc.localidadCliente.trim().toLowerCase() ===
            otro.localidadCliente.trim().toLowerCase();
        const mismaDestino =
          inc.empresaNombre &&
          otro.empresaNombre &&
          inc.empresaNombre.trim().toLowerCase() ===
            otro.empresaNombre.trim().toLowerCase() &&
          inc.sucursalNombre &&
          otro.sucursalNombre &&
          inc.sucursalNombre.trim().toLowerCase() ===
            otro.sucursalNombre.trim().toLowerCase();
        if (mismaLocalidad || mismaDestino) ids.add(inc.id);
      }
    }
  }
  return ids;
}

function EstadoValidacionBadge({ estado }: { estado: string }) {
  if (estado === "ok")
    return <span className="font-body text-xs font-semibold text-success">● OK</span>;
  if (estado === "con_alertas")
    return <span className="font-body text-xs font-semibold text-destructive">● CON ALERTAS</span>;
  return <span className="font-body text-xs text-muted-foreground">{estado}</span>;
}

function TipoBadge({ tipo }: { tipo: string }) {
  const lower = tipo.toLowerCase();
  const cls =
    lower === "correctivo"
      ? "bg-brand-orange/15 text-brand-orange"
      : lower === "preventivo"
        ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400"
        : "";
  return cls ? (
    <span className={`rounded-[6px] px-2 py-0.5 font-body text-xs font-semibold ${cls}`}>
      {tipo}
    </span>
  ) : (
    <span className="font-body text-xs text-muted-foreground">{tipo}</span>
  );
}

function riesgoClass(riesgo: number) {
  if (riesgo > 0.7) return "text-destructive";
  if (riesgo > 0.3) return "text-warning";
  return "text-success";
}

function AlertaSubRow({ alerta }: { alerta: Alerta }) {
  const tdCls = "py-2 px-4 font-body text-xs";
  return (
    <tr className="border-l-[3px] border-l-destructive/30 bg-destructive/[0.04]">
      <td className={cn(tdCls, "pl-7")} colSpan={3}>
        <span className="font-semibold text-foreground">{alerta.tipoAlerta}</span>
        {alerta.descripcion && (
          <span className="ml-2 text-muted-foreground">{alerta.descripcion}</span>
        )}
      </td>
      <td className={cn(tdCls, "text-right", riesgoClass(alerta.riesgo))}>
        {Math.round(alerta.riesgo * 100)}%
      </td>
      <td className={`${tdCls} text-muted-foreground`} colSpan={4}>
        {alerta.estado}
      </td>
    </tr>
  );
}

function IncidenteRow({
  incidente,
  alertasInc,
  expanded,
  isRutaCompartida,
  onToggle,
}: {
  incidente: Incidente;
  alertasInc: Alerta[];
  expanded: boolean;
  isRutaCompartida: boolean;
  onToggle: () => void;
}) {
  const tdCls = "py-3 px-4 font-body text-sm text-foreground";
  const diff =
    incidente.costoServicioEsperado !== null
      ? incidente.costoServicioCobrado - incidente.costoServicioEsperado
      : null;
  const hasAlertas = alertasInc.length > 0;
  return (
    <>
      <tr
        className={cn(
          "border-t border-border transition-colors hover:bg-muted/30",
          hasAlertas ? "cursor-pointer" : "cursor-default",
        )}
        onClick={hasAlertas ? onToggle : undefined}
      >
        <td className={tdCls}>
          <div className="flex items-center gap-1.5">
            {hasAlertas &&
              (expanded ? (
                <ChevronDown size={12} className="flex-shrink-0 text-muted-foreground" />
              ) : (
                <ChevronRight size={12} className="flex-shrink-0 text-muted-foreground" />
              ))}
            <a
                href={incidentUrl(incidente.numeroIncidente)}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="text-brand-orange hover:underline"
              >
                {incidente.numeroIncidente}
              </a>
          </div>
        </td>
        <td className={tdCls}>
          <div className="flex items-center gap-1.5">
            <span>
              {[incidente.empresaNombre, incidente.sucursalNombre].filter(Boolean).join(" / ") ||
                "—"}
            </span>
            {isRutaCompartida && (
              <span title="Posible ruta compartida: otro incidente del mismo día comparte destino o localidad">
                <Route size={12} className="flex-shrink-0 text-brand-orange" />
              </span>
            )}
            {incidente.urlMaps && (
              <a
                href={incidente.urlMaps}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                title="Ver en Google Maps"
                className="text-brand-orange hover:opacity-80"
              >
                <ExternalLink size={12} />
              </a>
            )}
          </div>
          {incidente.localidadCliente && (
            <div className="mt-0.5 font-body text-xs text-muted-foreground">
              {incidente.localidadCliente}
            </div>
          )}
        </td>
        <td className={tdCls}>
          <TipoBadge tipo={incidente.tipo} />
        </td>
        <td className={`${tdCls} text-right`}>{formatARS(incidente.costoServicioCobrado)}</td>
        <td className={`${tdCls} text-right text-muted-foreground`}>
          {incidente.costoServicioEsperado !== null
            ? formatARS(incidente.costoServicioEsperado)
            : "—"}
        </td>
        <td
          className={cn(
            `${tdCls} text-right`,
            diff !== null && (diff > 0 ? "text-destructive" : "text-success"),
          )}
        >
          {diff !== null ? formatARS(diff) : "—"}
        </td>
        <td className={`${tdCls} text-muted-foreground`}>
          {incidente.fechaCierre ? formatFecha(incidente.fechaCierre) : "—"}
        </td>
        <td className={tdCls}>
          <EstadoValidacionBadge estado={incidente.estadoValidacion} />
        </td>
      </tr>
      {expanded && alertasInc.map((a) => <AlertaSubRow key={a.id} alerta={a} />)}
    </>
  );
}

export function IncidentesSeccion({
  titulo,
  accentClass,
  incidentes,
  alertasByInc,
  soloConAlertas,
}: {
  titulo: string;
  accentClass?: string;
  incidentes: Incidente[];
  alertasByInc: Record<string, Alerta[]>;
  soloConAlertas?: boolean;
}) {
  const [filtroFecha, setFiltroFecha] = useState("");
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const rutasCompartidas = useMemo(() => computeRutasCompartidas(incidentes), [incidentes]);

  const fechas = Array.from(
    new Set(incidentes.map((i) => i.fechaCierre).filter((f): f is string => !!f)),
  ).sort();

  const filtrados = useMemo(() => {
    const base = soloConAlertas
      ? incidentes.filter((i) => (alertasByInc[i.id] ?? []).length > 0)
      : incidentes;
    return filtroFecha ? base.filter((i) => i.fechaCierre === filtroFecha) : base;
  }, [incidentes, alertasByInc, soloConAlertas, filtroFecha]);

  const totalServicio = filtrados.reduce((s, i) => s + i.costoServicioCobrado, 0);
  const totalKms = filtrados.reduce((s, i) => s + i.cantKmCobrado, 0);
  const totalGeneral = filtrados.reduce((s, i) => s + i.costoTotalCobrado, 0);

  const toggleExpanded = (incId: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(incId)) next.delete(incId);
      else next.add(incId);
      return next;
    });
  };

  const thCls =
    "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 font-heading text-base font-bold text-foreground">
          {accentClass && <span className={cn("text-lg leading-none", accentClass)}>■</span>}
          {titulo}
          <span className="font-body text-sm font-normal text-muted-foreground">
            {incidentes.length.toLocaleString("es-AR")}
          </span>
        </h2>
        {fechas.length > 1 && (
          <label className="flex items-center gap-2 font-body text-xs text-muted-foreground">
            Filtrar por fecha de cierre:
            <select
              value={filtroFecha}
              onChange={(e) => setFiltroFecha(e.target.value)}
              className="rounded-[8px] border border-border bg-card px-2 py-1 font-body text-xs text-foreground outline-none focus:border-brand-orange/50"
            >
              <option value="">Todas</option>
              {fechas.map((f) => (
                <option key={f} value={f}>
                  {formatFecha(f)}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
      <div className="overflow-hidden rounded-[12px] border border-border bg-card">
        {filtrados.length === 0 ? (
          <p className="px-4 py-6 font-body text-sm text-muted-foreground">Sin incidentes.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-muted/40">
                  <th className={thCls}>Nro Incidente</th>
                  <th className={thCls}>Empresa / Sucursal</th>
                  <th className={thCls}>Tipo</th>
                  <th className={`${thCls} text-right`}>Cobrado</th>
                  <th className={`${thCls} text-right`}>Esperado</th>
                  <th className={`${thCls} text-right`}>Diferencia</th>
                  <th className={thCls}>Fecha</th>
                  <th className={thCls}>Estado</th>
                </tr>
              </thead>
              <tbody>
                {filtrados.map((inc) => (
                  <IncidenteRow
                    key={inc.id}
                    incidente={inc}
                    alertasInc={alertasByInc[inc.id] ?? []}
                    expanded={expandedIds.has(inc.id)}
                    isRutaCompartida={rutasCompartidas.has(inc.id)}
                    onToggle={() => toggleExpanded(inc.id)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
        {filtrados.length > 0 && (
          <div className="flex flex-wrap items-center justify-end gap-6 border-t border-border bg-muted/40 px-4 py-3 font-body text-sm">
            <span className="text-muted-foreground">
              Costo servicio: <span className="text-foreground">{formatARS(totalServicio)}</span>
            </span>
            <span className="text-muted-foreground">
              KMs: <span className="text-foreground">{totalKms.toLocaleString("es-AR")}</span>
            </span>
            <span className="text-muted-foreground">
              Total general:{" "}
              <span className="font-semibold text-foreground">{formatARS(totalGeneral)}</span>
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
