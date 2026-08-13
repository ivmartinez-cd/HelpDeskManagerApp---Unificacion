"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Spinner } from "@/shared/components/ui/spinner";
import { cn } from "@/shared/utils/cn";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  Alerta,
  EstadoLiquidacion,
  Liquidacion,
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

function Kpi({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "success" | "destructive";
}) {
  return (
    <div className="flex flex-col">
      <span className="font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground">
        {label}
      </span>
      <span
        className={cn(
          "font-heading text-2xl font-extrabold",
          tone === "success" ? "text-success" : tone === "destructive" ? "text-destructive" : "text-foreground",
        )}
      >
        {value}
      </span>
    </div>
  );
}

function ExtraItemSeccion({
  liquidacion,
  onUpdated,
}: {
  liquidacion: Liquidacion;
  onUpdated: (updated: Liquidacion) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [concepto, setConcepto] = useState(liquidacion.conceptoExtra ?? "");
  const [monto, setMonto] = useState(liquidacion.montoExtra?.toString() ?? "");
  const [saving, setSaving] = useState(false);

  const inputCls =
    "rounded-[8px] border border-border bg-background px-3 py-1.5 font-body text-sm text-foreground outline-none focus:border-brand-orange/50";

  const handleSave = async () => {
    setSaving(true);
    try {
      const montoNum = monto.trim() !== "" ? parseFloat(monto) : null;
      const conceptoVal = concepto.trim() !== "" ? concepto.trim() : null;
      const updated = await liquidacionesApi.updateExtra(liquidacion.id, {
        conceptoExtra: conceptoVal,
        montoExtra: montoNum,
      });
      onUpdated(updated);
      setEditing(false);
    } catch {
      toast.error("Error al guardar el ítem extra");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setConcepto(liquidacion.conceptoExtra ?? "");
    setMonto(liquidacion.montoExtra?.toString() ?? "");
    setEditing(false);
  };

  const totalAjustado = liquidacion.totalImporte + (liquidacion.montoExtra ?? 0);

  return (
    <div className="rounded-[12px] border border-border bg-card p-5">
      <div className="flex items-center justify-between gap-4">
        <span className="font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground">
          Ítem extra
        </span>
        {!editing && (
          <button
            onClick={() => setEditing(true)}
            className="font-body text-xs text-brand-orange hover:underline"
          >
            {liquidacion.montoExtra != null ? "Editar" : "Agregar"}
          </button>
        )}
      </div>

      {editing ? (
        <div className="mt-3 flex flex-wrap items-end gap-3">
          <div className="flex flex-col gap-1">
            <label className="font-body text-xs text-muted-foreground">Concepto</label>
            <input
              value={concepto}
              onChange={(e) => setConcepto(e.target.value)}
              placeholder="Ej. Seguro de viaje"
              className={`${inputCls} w-56`}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="font-body text-xs text-muted-foreground">Monto ($)</label>
            <input
              type="number"
              value={monto}
              onChange={(e) => setMonto(e.target.value)}
              placeholder="0.00"
              className={`${inputCls} w-32`}
            />
          </div>
          <button
            onClick={() => void handleSave()}
            disabled={saving}
            className="rounded-[8px] bg-brand-orange px-4 py-1.5 font-body text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
          >
            {saving ? "Guardando..." : "Guardar"}
          </button>
          <button
            onClick={handleCancel}
            disabled={saving}
            className="font-body text-sm text-muted-foreground hover:text-foreground disabled:opacity-50"
          >
            Cancelar
          </button>
        </div>
      ) : liquidacion.montoExtra != null ? (
        <div className="mt-2 flex flex-wrap items-baseline gap-6">
          <div className="flex flex-col">
            <span className="font-body text-sm text-foreground">
              {liquidacion.conceptoExtra ?? "—"}
            </span>
            <span className="font-heading text-xl font-extrabold text-foreground">
              {formatARS(liquidacion.montoExtra)}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground">
              Total ajustado
            </span>
            <span className="font-heading text-xl font-extrabold text-foreground">
              {formatARS(totalAjustado)}
            </span>
          </div>
        </div>
      ) : (
        <p className="mt-2 font-body text-sm text-muted-foreground">Sin ítem extra.</p>
      )}
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

  const handleUpdateExtra = (updated: Liquidacion) => {
    if (!detalle) return;
    setDetalle({ ...detalle, liquidacion: updated });
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
        className="flex w-fit items-center gap-1.5 font-body text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        ← Lista de liquidaciones
      </Link>

      {/* Header */}
      <div className="rounded-[12px] border border-border bg-card p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-2">
            <h1 className="font-heading text-xl font-extrabold text-foreground">
              {liquidacion.nombreArchivo ?? `Liquidación ${liquidacion.periodo}`}
            </h1>
            <div className="flex flex-wrap items-center gap-3 font-body text-sm text-muted-foreground">
              {pst && (
                <span>
                  {pst.region ?? pst.nombreCorto} — {pst.nombre}
                </span>
              )}
              <span>·</span>
              <span>{liquidacion.periodo}</span>
              <span>·</span>
              <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 font-body text-xs text-muted-foreground">
                {liquidacion.tipoLiquidacion}
              </span>
              <span>·</span>
              <select
                value={liquidacion.estado}
                disabled={updatingEstado}
                onChange={(e) => void handleUpdateEstado(e.target.value as EstadoLiquidacion)}
                className="rounded-[8px] border border-border bg-card px-2 py-1 font-body text-xs text-foreground outline-none focus:border-brand-orange/50 disabled:opacity-50"
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
                tone={liquidacion.totalAlertas > 0 ? "destructive" : "success"}
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

      <ExtraItemSeccion liquidacion={liquidacion} onUpdated={handleUpdateExtra} />

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
