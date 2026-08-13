"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, ExternalLink } from "lucide-react";
import type { Alerta, Incidente } from "../types/liquidaciones";
import { formatARS, formatFecha } from "../lib/format";

function EstadoValidacionBadge({ estado }: { estado: string }) {
  if (estado === "ok") {
    return (
      <span
        className="inline-flex items-center rounded-full px-2 py-0.5 font-body text-xs font-semibold"
        style={{ background: "rgba(34,197,94,.15)", color: "#4ade80" }}
      >
        OK
      </span>
    );
  }
  if (estado === "con_alertas") {
    return (
      <span
        className="inline-flex items-center rounded-full px-2 py-0.5 font-body text-xs font-semibold"
        style={{ background: "rgba(239,68,68,.15)", color: "#ef4444" }}
      >
        Con alertas
      </span>
    );
  }
  return (
    <span className="font-body text-xs" style={{ color: "rgba(255,255,255,.4)" }}>
      {estado}
    </span>
  );
}

function AlertaSubRow({ alerta }: { alerta: Alerta }) {
  const tdCls = "py-2 px-4 font-body text-xs";
  const riesgoColor =
    alerta.riesgo > 0.7 ? "#ef4444" : alerta.riesgo > 0.3 ? "#eab308" : "#4ade80";
  return (
    <tr style={{ background: "rgba(239,68,68,.04)", borderLeft: "3px solid rgba(239,68,68,.3)" }}>
      <td className={tdCls} colSpan={3} style={{ paddingLeft: 28 }}>
        <span className="font-semibold" style={{ color: "#e0e0e0" }}>
          {alerta.tipoAlerta}
        </span>
        {alerta.descripcion && (
          <span className="ml-2" style={{ color: "rgba(255,255,255,.5)" }}>
            {alerta.descripcion}
          </span>
        )}
      </td>
      <td className={`${tdCls} text-right`} style={{ color: riesgoColor }}>
        {Math.round(alerta.riesgo * 100)}%
      </td>
      <td className={tdCls} colSpan={4} style={{ color: "rgba(255,255,255,.35)" }}>
        {alerta.estado}
      </td>
    </tr>
  );
}

function IncidenteRow({
  incidente,
  alertasInc,
  expanded,
  onToggle,
}: {
  incidente: Incidente;
  alertasInc: Alerta[];
  expanded: boolean;
  onToggle: () => void;
}) {
  const tdCls = "py-3 px-4 font-body text-sm";
  const diff =
    incidente.costoServicioEsperado !== null
      ? incidente.costoServicioCobrado - incidente.costoServicioEsperado
      : null;
  const hasAlertas = alertasInc.length > 0;
  return (
    <>
      <tr
        className="border-t transition-colors hover:bg-white/[0.03]"
        style={{ borderColor: "rgba(255,255,255,.07)", cursor: hasAlertas ? "pointer" : "default" }}
        onClick={hasAlertas ? onToggle : undefined}
      >
        <td className={tdCls}>
          <div className="flex items-center gap-1.5">
            {hasAlertas &&
              (expanded ? (
                <ChevronDown size={12} style={{ color: "rgba(255,255,255,.4)", flexShrink: 0 }} />
              ) : (
                <ChevronRight size={12} style={{ color: "rgba(255,255,255,.4)", flexShrink: 0 }} />
              ))}
            <span style={{ color: "#e0e0e0" }}>{incidente.numeroIncidente}</span>
          </div>
        </td>
        <td className={tdCls} style={{ color: "#e0e0e0" }}>
          <div className="flex items-center gap-1.5">
            <span>
              {[incidente.empresaNombre, incidente.sucursalNombre].filter(Boolean).join(" / ") ||
                "—"}
            </span>
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
            <div className="mt-0.5 font-body text-xs" style={{ color: "rgba(255,255,255,.4)" }}>
              {incidente.localidadCliente}
            </div>
          )}
        </td>
        <td className={tdCls} style={{ color: "rgba(255,255,255,.5)" }}>
          {incidente.tipo}
        </td>
        <td className={`${tdCls} text-right`} style={{ color: "#e0e0e0" }}>
          {formatARS(incidente.costoServicioCobrado)}
        </td>
        <td className={`${tdCls} text-right`} style={{ color: "rgba(255,255,255,.5)" }}>
          {incidente.costoServicioEsperado !== null
            ? formatARS(incidente.costoServicioEsperado)
            : "—"}
        </td>
        <td
          className={`${tdCls} text-right`}
          style={{ color: diff === null ? "#e0e0e0" : diff > 0 ? "#ef4444" : "#4ade80" }}
        >
          {diff !== null ? formatARS(diff) : "—"}
        </td>
        <td className={tdCls} style={{ color: "rgba(255,255,255,.4)" }}>
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
  incidentes,
  alertasByInc,
}: {
  titulo: string;
  incidentes: Incidente[];
  alertasByInc: Record<string, Alerta[]>;
}) {
  const [filtroFecha, setFiltroFecha] = useState("");
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const fechas = Array.from(
    new Set(incidentes.map((i) => i.fechaCierre).filter((f): f is string => !!f)),
  ).sort();
  const filtrados = filtroFecha
    ? incidentes.filter((i) => i.fechaCierre === filtroFecha)
    : incidentes;
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
        <h2 className="font-heading text-base font-bold text-foreground">
          {titulo}
          <span className="ml-2 font-body text-sm font-normal" style={{ color: "rgba(255,255,255,.4)" }}>
            {filtrados.length.toLocaleString("es-AR")}
          </span>
        </h2>
        {fechas.length > 1 && (
          <label className="flex items-center gap-2 font-body text-xs" style={{ color: "rgba(255,255,255,.5)" }}>
            Filtrar por fecha de cierre:
            <select
              value={filtroFecha}
              onChange={(e) => setFiltroFecha(e.target.value)}
              className="rounded-[8px] border border-white/10 bg-white/5 px-2 py-1 font-body text-xs text-foreground outline-none focus:border-brand-orange/50"
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
      <div
        className="overflow-hidden rounded-[12px]"
        style={{ background: "#1e1e1e", border: "1px solid rgba(255,255,255,.07)" }}
      >
        {filtrados.length === 0 ? (
          <p className="px-4 py-6 font-body text-sm text-muted-foreground">Sin incidentes.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ background: "rgba(0,0,0,.2)" }}>
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
                    onToggle={() => toggleExpanded(inc.id)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
        {filtrados.length > 0 && (
          <div
            className="flex flex-wrap items-center justify-end gap-6 border-t px-4 py-3 font-body text-sm"
            style={{ borderColor: "rgba(255,255,255,.07)", background: "rgba(0,0,0,.2)" }}
          >
            <span style={{ color: "rgba(255,255,255,.5)" }}>
              Costo servicio: <span style={{ color: "#e0e0e0" }}>{formatARS(totalServicio)}</span>
            </span>
            <span style={{ color: "rgba(255,255,255,.5)" }}>
              KMs: <span style={{ color: "#e0e0e0" }}>{totalKms.toLocaleString("es-AR")}</span>
            </span>
            <span style={{ color: "rgba(255,255,255,.5)" }}>
              Total general:{" "}
              <span className="font-semibold" style={{ color: "#e0e0e0" }}>
                {formatARS(totalGeneral)}
              </span>
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
