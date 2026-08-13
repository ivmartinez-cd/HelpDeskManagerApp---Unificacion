"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Badge, type BadgeVariant } from "@/shared/components/ui/badge";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { EstadoObservacion, Observacion } from "../types/liquidaciones";
import { formatARS } from "../lib/format";

const ESTADO_STYLES: Record<EstadoObservacion, { variant: BadgeVariant; label: string }> = {
  pendiente: { variant: "warning", label: "Pendiente" },
  en_revision: { variant: "info", label: "En revisión" },
  resuelta: { variant: "success", label: "Resuelta" },
  rechazada: { variant: "danger", label: "Rechazada" },
  excepcion_aprobada: { variant: "accent", label: "Excepción aprobada" },
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

function severidadVariant(severidad: string): BadgeVariant {
  if (severidad === "CRITICO") return "danger";
  if (severidad === "ADVERTENCIA") return "warning";
  return "success";
}

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
  const tdCls = "py-3 px-4 font-body text-sm text-foreground";
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
    <tr className="border-t border-border">
      <td className={tdCls}>
        <Badge variant={severidadVariant(obs.severidad)}>{obs.severidad}</Badge>
      </td>
      <td className={tdCls}>
        <div className="font-semibold">{obs.titulo}</div>
        {obs.descripcion && (
          <div className="mt-0.5 text-xs text-muted-foreground">{obs.descripcion}</div>
        )}
      </td>
      <td className={`${tdCls} text-right`}>{formatARS(obs.montoCobrado)}</td>
      <td className={`${tdCls} text-right text-muted-foreground`}>
        {formatARS(obs.montoEsperado)}
      </td>
      <td
        className={`${tdCls} text-right ${obs.diferencia > 0 ? "text-destructive" : "text-success"}`}
      >
        {formatARS(obs.diferencia)}
      </td>
      <td className={tdCls}>
        <Badge variant={estadoStyle.variant}>{estadoStyle.label}</Badge>
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
        <span className="ml-2 font-body text-sm font-normal text-muted-foreground">
          {observaciones.length.toLocaleString("es-AR")}
        </span>
      </h2>
      <div className="overflow-hidden rounded-[12px] border border-border bg-card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-muted/40">
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
