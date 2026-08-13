"use client";

import { useState } from "react";
import { toast } from "sonner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { EstadoObservacion, Observacion } from "../types/liquidaciones";
import { formatARS } from "../lib/format";

const ESTADO_STYLES: Record<EstadoObservacion, { bg: string; fg: string; label: string }> = {
  pendiente: { bg: "rgba(234,179,8,.15)", fg: "#eab308", label: "Pendiente" },
  en_revision: { bg: "rgba(59,130,246,.15)", fg: "#60a5fa", label: "En revisión" },
  resuelta: { bg: "rgba(34,197,94,.15)", fg: "#4ade80", label: "Resuelta" },
  rechazada: { bg: "rgba(239,68,68,.15)", fg: "#ef4444", label: "Rechazada" },
  excepcion_aprobada: { bg: "rgba(168,85,247,.15)", fg: "#c084fc", label: "Excepción aprobada" },
};

// Transiciones del legacy (ObservacionCard): pendiente → revisar/aprobar excepción/
// resolver; en_revisión → aprobar excepción/rechazar/resolver; estados finales → reabrir.
const TRANSICIONES: Record<EstadoObservacion, { estado: EstadoObservacion; label: string }[]> = {
  pendiente: [
    { estado: "en_revision", label: "Revisar" },
    { estado: "excepcion_aprobada", label: "Aprobar excepción" },
    { estado: "resuelta", label: "Resolver" },
  ],
  en_revision: [
    { estado: "excepcion_aprobada", label: "Aprobar excepción" },
    { estado: "rechazada", label: "Rechazar" },
    { estado: "resuelta", label: "Resolver" },
  ],
  resuelta: [{ estado: "en_revision", label: "Reabrir" }],
  rechazada: [{ estado: "en_revision", label: "Reabrir" }],
  excepcion_aprobada: [{ estado: "en_revision", label: "Reabrir" }],
};

function ObservacionRow({
  liquidacionId,
  obs,
  onChanged,
}: {
  liquidacionId: string;
  obs: Observacion;
  onChanged: () => void;
}) {
  const [updating, setUpdating] = useState(false);
  const tdCls = "py-3 px-4 font-body text-sm";
  const sevColor =
    obs.severidad === "CRITICO"
      ? "#ef4444"
      : obs.severidad === "ADVERTENCIA"
        ? "#eab308"
        : "#4ade80";
  const estadoStyle = ESTADO_STYLES[obs.estado] ?? ESTADO_STYLES.pendiente;

  const handleEstado = async (nuevo: EstadoObservacion) => {
    setUpdating(true);
    try {
      await liquidacionesApi.updateEstadoObservacion(liquidacionId, obs.id, nuevo);
      onChanged();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al cambiar el estado");
    } finally {
      setUpdating(false);
    }
  };

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
      <td className={tdCls}>
        <span
          className="inline-flex items-center rounded-full px-2 py-0.5 font-body text-xs font-semibold"
          style={{ background: estadoStyle.bg, color: estadoStyle.fg }}
        >
          {estadoStyle.label}
        </span>
      </td>
      <td className={`${tdCls} text-right whitespace-nowrap`}>
        {(TRANSICIONES[obs.estado] ?? []).map((t) => (
          <button
            key={t.estado}
            disabled={updating}
            onClick={() => void handleEstado(t.estado)}
            className="ml-3 font-body text-xs text-brand-orange hover:underline disabled:opacity-50"
          >
            {t.label}
          </button>
        ))}
      </td>
    </tr>
  );
}

export function ObservacionesSeccion({
  liquidacionId,
  observaciones,
  onChanged,
}: {
  liquidacionId: string;
  observaciones: Observacion[];
  onChanged: () => void;
}) {
  const thCls =
    "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
  if (observaciones.length === 0) return null;
  return (
    <div className="flex flex-col gap-3">
      <h2 className="font-heading text-base font-bold text-foreground">
        Observaciones
        <span className="ml-2 font-body text-sm font-normal" style={{ color: "rgba(255,255,255,.4)" }}>
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
                <th className={`${thCls} text-right`}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {observaciones.map((obs) => (
                <ObservacionRow
                  key={obs.id}
                  liquidacionId={liquidacionId}
                  obs={obs}
                  onChanged={onChanged}
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
