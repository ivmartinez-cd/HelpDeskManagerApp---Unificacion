"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight, ExternalLink, Route } from "lucide-react";
import { Badge } from "@/shared/components/ui/badge";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { cn } from "@/shared/utils/cn";
import { compareSortValues, useTableSort } from "@/shared/hooks/use-table-sort";
import type { Alerta, Incidente } from "../types/liquidaciones";
import { ESTADO_ALERTA_STYLES } from "../lib/alerta-estados";
import { formatARS, formatFecha } from "../lib/format";
import { incidentUrl } from "@/shared/utils/incident-link";

export function computeRutasCompartidas(incidentes: Incidente[]): Set<string> {
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

export function computeSeriesDuplicadas(incidentes: Incidente[]): Set<string> {
  const ids = new Set<string>();
  const bySerie = new Map<string, string[]>();
  for (const inc of incidentes) {
    if (!inc.nroSerie) continue;
    const list = bySerie.get(inc.nroSerie) ?? [];
    list.push(inc.id);
    bySerie.set(inc.nroSerie, list);
  }
  for (const incIds of bySerie.values()) {
    if (incIds.length > 1) {
      for (const id of incIds) ids.add(id);
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
  const estilo = ESTADO_ALERTA_STYLES[alerta.estado] ?? ESTADO_ALERTA_STYLES.pendiente;
  return (
    <tr className="border-l-[3px] border-l-destructive/30 bg-destructive/[0.04]">
      <td className={cn(tdCls, "pl-7")} colSpan={4}>
        <span className="font-semibold text-foreground">{alerta.tipoAlerta}</span>
        {alerta.descripcion && (
          <span className="ml-2 text-muted-foreground">{alerta.descripcion}</span>
        )}
        {alerta.justificacion && (
          <span className="ml-2 italic text-muted-foreground" title={alerta.justificacion}>
            ·{" "}
            {alerta.justificacion.length > 60
              ? `${alerta.justificacion.slice(0, 60)}…`
              : alerta.justificacion}
          </span>
        )}
      </td>
      <td className={cn(tdCls, "text-right", riesgoClass(alerta.riesgo))}>
        {Math.round(alerta.riesgo * 100)}%
      </td>
      <td className={tdCls} colSpan={6}>
        <span className="flex items-center gap-3">
          <Badge variant={estilo.variant}>{estilo.label}</Badge>
          <a href="#alertas" className="font-semibold text-brand-orange hover:underline">
            Gestionar
          </a>
        </span>
      </td>
    </tr>
  );
}

function IncidenteRow({
  incidente,
  alertasInc,
  expanded,
  isRutaCompartida,
  isSeriesDuplicada,
  onToggle,
}: {
  incidente: Incidente;
  alertasInc: Alerta[];
  expanded: boolean;
  isRutaCompartida: boolean;
  isSeriesDuplicada: boolean;
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
          {incidente.nroSerie ? (
            <span className={cn(isSeriesDuplicada && "font-semibold text-warning")}>
              {incidente.nroSerie}
              {isSeriesDuplicada && (
                <span className="ml-1" title="Nro de serie duplicado en esta liquidación">
                  ⚠
                </span>
              )}
            </span>
          ) : (
            <span className="text-muted-foreground">—</span>
          )}
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
        <td className={`${tdCls} text-right`}>
          {Math.round(incidente.cantKmCobrado).toLocaleString("es-AR")}
        </td>
        <td className={`${tdCls} text-right`}>
          {incidente.cantKmEsperado !== null ? (
            <span className="font-semibold text-success">
              {Math.round(incidente.cantKmEsperado).toLocaleString("es-AR")}
            </span>
          ) : (
            <span className="text-xs font-semibold text-warning">Sin tabla</span>
          )}
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

type IncSortKey =
  | "incidente"
  | "serie"
  | "empresa"
  | "tipo"
  | "kmCobrado"
  | "kmEsperado"
  | "cobrado"
  | "esperado"
  | "diferencia"
  | "fecha";

const INC_SORT_KEYS: readonly IncSortKey[] = [
  "incidente", "serie", "empresa", "tipo",
  "kmCobrado", "kmEsperado", "cobrado", "esperado", "diferencia", "fecha",
];

export function IncidentesTabla({
  incidentes,
  allIncidentes,
  alertasByInc,
}: {
  incidentes: Incidente[];
  allIncidentes: Incidente[];
  alertasByInc: Record<string, Alerta[]>;
}) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const { sort, toggleSort } = useTableSort<IncSortKey>({
    initial: { key: "incidente", direction: "asc" },
    keys: INC_SORT_KEYS,
    descFirstKeys: ["kmCobrado", "kmEsperado", "cobrado", "esperado", "diferencia", "fecha"],
  });

  const rutasCompartidas = useMemo(() => computeRutasCompartidas(allIncidentes), [allIncidentes]);
  const seriesDuplicadas = useMemo(() => computeSeriesDuplicadas(allIncidentes), [allIncidentes]);

  const sorted = useMemo(() => {
    return [...incidentes].sort((a, b) => {
      const getSv = (inc: Incidente) => {
        switch (sort.key) {
          case "incidente": return inc.numeroIncidente;
          case "serie": return inc.nroSerie ?? null;
          case "empresa":
            return [inc.empresaNombre, inc.sucursalNombre].filter(Boolean).join(" / ") || null;
          case "tipo": return inc.tipo;
          case "kmCobrado": return inc.cantKmCobrado;
          case "kmEsperado": return inc.cantKmEsperado;
          case "cobrado": return inc.costoServicioCobrado;
          case "esperado": return inc.costoServicioEsperado;
          case "diferencia":
            return inc.costoServicioEsperado !== null
              ? inc.costoServicioCobrado - inc.costoServicioEsperado
              : null;
          case "fecha": return inc.fechaCierre ?? null;
        }
      };
      return compareSortValues(getSv(a), getSv(b), sort.direction);
    });
  }, [incidentes, sort]);

  const toggleExpanded = (incId: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(incId)) next.delete(incId);
      else next.add(incId);
      return next;
    });
  };

  const totalKms = incidentes.reduce((s, i) => s + i.cantKmCobrado, 0);
  const totalServicio = incidentes.reduce((s, i) => s + i.costoServicioCobrado, 0);
  const totalGeneral = incidentes.reduce((s, i) => s + i.costoTotalCobrado, 0);

  const thCls =
    "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";

  if (incidentes.length === 0) {
    return (
      <div className="overflow-hidden rounded-[12px] border border-border bg-card">
        <p className="px-4 py-6 font-body text-sm text-muted-foreground">Sin incidentes.</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-muted/40">
              <SortableHeader column={{ key: "incidente", label: "Nro Incidente" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "serie", label: "Nro Serie" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "empresa", label: "Empresa / Sucursal" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "tipo", label: "Tipo" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "kmCobrado", label: "KMs cob." }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "kmEsperado", label: "KMs esp." }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "cobrado", label: "Cobrado" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "esperado", label: "Esperado" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "diferencia", label: "Diferencia" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "fecha", label: "Fecha" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <th className={thCls}>Estado</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((inc) => (
              <IncidenteRow
                key={inc.id}
                incidente={inc}
                alertasInc={alertasByInc[inc.id] ?? []}
                expanded={expandedIds.has(inc.id)}
                isRutaCompartida={rutasCompartidas.has(inc.id)}
                isSeriesDuplicada={seriesDuplicadas.has(inc.id)}
                onToggle={() => toggleExpanded(inc.id)}
              />
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex flex-wrap items-center justify-end gap-6 border-t border-border bg-muted/40 px-4 py-3 font-body text-sm">
        <span className="text-muted-foreground">
          KMs: <span className="text-foreground">{Math.round(totalKms).toLocaleString("es-AR")}</span>
        </span>
        <span className="text-muted-foreground">
          Costo servicio: <span className="text-foreground">{formatARS(totalServicio)}</span>
        </span>
        <span className="text-muted-foreground">
          Total general:{" "}
          <span className="font-semibold text-foreground">{formatARS(totalGeneral)}</span>
        </span>
      </div>
    </div>
  );
}
