"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  Alerta,
  EstadoLiquidacion,
  Incidente,
  LiquidacionDetalle,
  Observacion,
  PrestadorLiquidacion,
} from "../types/liquidaciones";

function formatARS(n: number) {
  return n.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 2 });
}

function formatFecha(iso: string) {
  const d = new Date(iso);
  return `${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()}`;
}

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
          {[incidente.empresaNombre, incidente.sucursalNombre].filter(Boolean).join(" / ") || "—"}
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

function ObservacionRow({ obs }: { obs: Observacion }) {
  const tdCls = "py-3 px-4 font-body text-sm";
  const sevColor =
    obs.severidad === "CRITICO"
      ? "#ef4444"
      : obs.severidad === "ADVERTENCIA"
        ? "#eab308"
        : "#4ade80";
  return (
    <tr className="border-t" style={{ borderColor: "rgba(255,255,255,.07)" }}>
      <td className={tdCls}>
        <span
          className="inline-flex items-center rounded-full px-2 py-0.5 font-body text-xs font-semibold"
          style={{ background: `${sevColor}20`, color: sevColor }}
        >
          {obs.severidad}
        </span>
      </td>
      <td className={tdCls} style={{ color: "#e0e0e0" }}>
        <div className="font-semibold">{obs.titulo}</div>
        {obs.descripcion && (
          <div className="mt-0.5 text-xs" style={{ color: "rgba(255,255,255,.5)" }}>
            {obs.descripcion}
          </div>
        )}
      </td>
      <td className={`${tdCls} text-right`} style={{ color: "#e0e0e0" }}>
        {formatARS(obs.montoCobrado)}
      </td>
      <td className={`${tdCls} text-right`} style={{ color: "rgba(255,255,255,.5)" }}>
        {formatARS(obs.montoEsperado)}
      </td>
      <td
        className={`${tdCls} text-right`}
        style={{ color: obs.diferencia > 0 ? "#ef4444" : "#4ade80" }}
      >
        {formatARS(obs.diferencia)}
      </td>
      <td className={tdCls} style={{ color: "rgba(255,255,255,.4)" }}>
        {obs.estado}
      </td>
    </tr>
  );
}

const ESTADOS: EstadoLiquidacion[] = [
  "abierta",
  "preliquidada",
  "recibida",
  "observada",
  "aprobada",
  "cerrada",
];

const ESTADO_LABELS: Record<EstadoLiquidacion, string> = {
  abierta: "Abierta",
  preliquidada: "Preliquidada",
  recibida: "Recibida",
  observada: "Observada",
  aprobada: "Aprobada",
  cerrada: "Cerrada",
};

export function LiquidacionDetalleView({ id }: { id: string }) {
  const [detalle, setDetalle] = useState<LiquidacionDetalle | null>(null);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [reanalizing, setReanalizing] = useState(false);
  const [updatingEstado, setUpdatingEstado] = useState(false);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [det, prest] = await Promise.all([
        liquidacionesApi.get(id),
        liquidacionesApi.listPrestadores(false),
      ]);
      setDetalle(det);
      setPrestadores(prest);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleReanalizar = async () => {
    setReanalizing(true);
    try {
      await liquidacionesApi.reanalyze(id);
      await load();
    } finally {
      setReanalizing(false);
    }
  };

  const handleUpdateEstado = async (nuevoEstado: EstadoLiquidacion) => {
    if (!detalle) return;
    setUpdatingEstado(true);
    try {
      const updated = await liquidacionesApi.updateEstado(id, nuevoEstado);
      setDetalle({ ...detalle, liquidacion: updated });
    } finally {
      setUpdatingEstado(false);
    }
  };

  const toggleExpanded = (incId: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(incId)) next.delete(incId);
      else next.add(incId);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (!detalle) return null;

  const { liquidacion, incidentes, alertas, observaciones } = detalle;
  const pstMap = Object.fromEntries(prestadores.map((p) => [p.id, p]));
  const pst = pstMap[liquidacion.prestadorId];
  const alertasByInc = alertas.reduce<Record<string, Alerta[]>>((acc, a) => {
    (acc[a.incidenteId] ??= []).push(a);
    return acc;
  }, {});

  const thCls =
    "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";

  return (
    <div className="flex flex-col gap-5 p-6">
      <Link
        href="/liquidaciones/lista"
        className="flex w-fit items-center gap-1.5 font-body text-sm transition-colors hover:text-foreground"
        style={{ color: "rgba(255,255,255,.4)" }}
      >
        ← Lista de liquidaciones
      </Link>

      {/* Header */}
      <div
        className="rounded-[12px] p-5"
        style={{ background: "#1e1e1e", border: "1px solid rgba(255,255,255,.07)" }}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-2">
            <h1 className="font-heading text-xl font-extrabold text-foreground">
              {liquidacion.nombreArchivo ?? `Liquidación ${liquidacion.periodo}`}
            </h1>
            <div
              className="flex flex-wrap items-center gap-3 font-body text-sm"
              style={{ color: "rgba(255,255,255,.6)" }}
            >
              {pst && (
                <span>
                  {pst.region ?? pst.nombreCorto} — {pst.nombre}
                </span>
              )}
              <span>·</span>
              <span>{liquidacion.periodo}</span>
              <span>·</span>
              <span
                className="inline-flex items-center rounded-full px-2 py-0.5 font-body text-xs"
                style={{ background: "rgba(255,255,255,.08)", color: "rgba(255,255,255,.5)" }}
              >
                {liquidacion.tipoLiquidacion}
              </span>
              <span>·</span>
              <select
                value={liquidacion.estado}
                disabled={updatingEstado}
                onChange={(e) => void handleUpdateEstado(e.target.value as EstadoLiquidacion)}
                className="rounded-[8px] border border-white/10 bg-white/5 px-2 py-1 font-body text-xs text-foreground outline-none focus:border-brand-orange/50 disabled:opacity-50"
              >
                {ESTADOS.map((e) => (
                  <option key={e} value={e}>
                    {ESTADO_LABELS[e]}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-8 pt-1">
              <div className="flex flex-col">
                <span
                  className="font-body text-[11px] font-bold uppercase tracking-[.06em]"
                  style={{ color: "#9a9a9a" }}
                >
                  Incidentes
                </span>
                <span className="font-heading text-2xl font-extrabold text-foreground">
                  {liquidacion.totalIncidentes.toLocaleString("es-AR")}
                </span>
              </div>
              <div className="flex flex-col">
                <span
                  className="font-body text-[11px] font-bold uppercase tracking-[.06em]"
                  style={{ color: "#9a9a9a" }}
                >
                  Alertas
                </span>
                <span
                  className="font-heading text-2xl font-extrabold"
                  style={{ color: liquidacion.totalAlertas > 0 ? "#ef4444" : "#4ade80" }}
                >
                  {liquidacion.totalAlertas.toLocaleString("es-AR")}
                </span>
              </div>
              <div className="flex flex-col">
                <span
                  className="font-body text-[11px] font-bold uppercase tracking-[.06em]"
                  style={{ color: "#9a9a9a" }}
                >
                  Total facturado
                </span>
                <span className="font-heading text-2xl font-extrabold text-foreground">
                  {formatARS(liquidacion.totalImporte)}
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={() => void handleReanalizar()}
            disabled={reanalizing}
            className="flex-shrink-0 rounded-[8px] bg-brand-orange px-4 py-2.5 font-body text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {reanalizing ? "Reanalizing..." : "↻ Reanalizar"}
          </button>
        </div>
      </div>

      {/* Incidentes */}
      <div className="flex flex-col gap-3">
        <h2 className="font-heading text-base font-bold text-foreground">
          Incidentes
          <span className="ml-2 font-body text-sm font-normal" style={{ color: "rgba(255,255,255,.4)" }}>
            {incidentes.length.toLocaleString("es-AR")}
          </span>
        </h2>
        <div
          className="overflow-hidden rounded-[12px]"
          style={{ background: "#1e1e1e", border: "1px solid rgba(255,255,255,.07)" }}
        >
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
                {incidentes.map((inc) => (
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
        </div>
      </div>

      {/* Observaciones */}
      {observaciones.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="font-heading text-base font-bold text-foreground">
            Observaciones
            <span
              className="ml-2 font-body text-sm font-normal"
              style={{ color: "rgba(255,255,255,.4)" }}
            >
              {observaciones.length.toLocaleString("es-AR")}
            </span>
          </h2>
          <div
            className="overflow-hidden rounded-[12px]"
            style={{ background: "#1e1e1e", border: "1px solid rgba(255,255,255,.07)" }}
          >
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr style={{ background: "rgba(0,0,0,.2)" }}>
                    <th className={thCls}>Severidad</th>
                    <th className={thCls}>Título</th>
                    <th className={`${thCls} text-right`}>Cobrado</th>
                    <th className={`${thCls} text-right`}>Esperado</th>
                    <th className={`${thCls} text-right`}>Diferencia</th>
                    <th className={thCls}>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {observaciones.map((obs) => (
                    <ObservacionRow key={obs.id} obs={obs} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
