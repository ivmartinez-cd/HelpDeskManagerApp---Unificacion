"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  Alerta,
  EstadoLiquidacion,
  LiquidacionDetalle,
  PrestadorLiquidacion,
} from "../types/liquidaciones";
import { formatARS } from "../lib/format";
import { IncidentesSeccion } from "./incidentes-seccion";
import { ObservacionesSeccion } from "./observaciones-seccion";

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

function Kpi({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex flex-col">
      <span
        className="font-body text-[11px] font-bold uppercase tracking-[.06em]"
        style={{ color: "#9a9a9a" }}
      >
        {label}
      </span>
      <span
        className="font-heading text-2xl font-extrabold"
        style={{ color: color ?? "#e0e0e0" }}
      >
        {value}
      </span>
    </div>
  );
}

export function LiquidacionDetalleView({ id }: { id: string }) {
  const [detalle, setDetalle] = useState<LiquidacionDetalle | null>(null);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [reanalizing, setReanalizing] = useState(false);
  const [updatingEstado, setUpdatingEstado] = useState(false);

  // Sin setLoading(true) sincrónico — ver nota en liquidaciones-lista.tsx.
  const load = useCallback(async () => {
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
  const correctivos = incidentes.filter((i) => i.tipo.toLowerCase() !== "preventivo");
  const preventivos = incidentes.filter((i) => i.tipo.toLowerCase() === "preventivo");

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
              <Kpi
                label="Incidentes"
                value={liquidacion.totalIncidentes.toLocaleString("es-AR")}
              />
              <Kpi
                label="Alertas"
                value={liquidacion.totalAlertas.toLocaleString("es-AR")}
                color={liquidacion.totalAlertas > 0 ? "#ef4444" : "#4ade80"}
              />
              <Kpi label="Total facturado" value={formatARS(liquidacion.totalImporte)} />
            </div>
          </div>
          <button
            onClick={() => void handleReanalizar()}
            disabled={reanalizing}
            className="flex-shrink-0 rounded-[8px] bg-brand-orange px-4 py-2.5 font-body text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {reanalizing ? "Reanalizando..." : "↻ Reanalizar"}
          </button>
        </div>
      </div>

      <IncidentesSeccion titulo="Correctivos" incidentes={correctivos} alertasByInc={alertasByInc} />
      {preventivos.length > 0 && (
        <IncidentesSeccion
          titulo="Preventivos"
          incidentes={preventivos}
          alertasByInc={alertasByInc}
        />
      )}

      <ObservacionesSeccion
        liquidacionId={id}
        observaciones={observaciones}
        onChanged={() => void load()}
      />
    </div>
  );
}
