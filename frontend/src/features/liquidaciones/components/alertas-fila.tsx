"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { liquidacionesApi } from "../api/liquidaciones-api";
import { CODIGO_ALT009, ESTADO_ALERTA_STYLES, TRANSICIONES_ALERTA } from "../lib/alerta-estados";
import type { Alerta, EstadoAlerta } from "../types/liquidaciones";

function riesgoClass(riesgo: number) {
  if (riesgo > 0.7) return "text-destructive";
  if (riesgo > 0.3) return "text-warning";
  return "text-success";
}

export function AlertaRow({
  liquidacionId,
  alerta,
  numeroIncidente,
  isSelected,
  onToggleSelect,
  onChanged,
  onDescartar,
  onResolverAlt009,
}: {
  liquidacionId: string;
  alerta: Alerta;
  numeroIncidente: string | null;
  isSelected: boolean;
  onToggleSelect: (id: string) => void;
  onChanged: () => void;
  onDescartar: (alerta: Alerta) => void;
  onResolverAlt009: (alerta: Alerta) => void;
}) {
  const [updating, setUpdating] = useState(false);
  const tdCls = "py-3 px-4 font-body text-sm text-foreground";
  const estilo = ESTADO_ALERTA_STYLES[alerta.estado] ?? ESTADO_ALERTA_STYLES.pendiente;

  const cambiar = async (estado: EstadoAlerta) => {
    setUpdating(true);
    try {
      await liquidacionesApi.updateEstadoAlerta(liquidacionId, alerta.id, { estado });
      onChanged();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al cambiar el estado");
    } finally {
      setUpdating(false);
    }
  };

  return (
    <tr className={`border-t border-border ${isSelected ? "bg-brand-orange/5" : ""}`}>
      <td className="py-3 px-4">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onToggleSelect(alerta.id)}
          aria-label={`Seleccionar alerta ${alerta.tipoAlerta}`}
          className="cursor-pointer accent-brand-orange"
        />
      </td>
      <td className={tdCls}>
        <span className="font-semibold">{alerta.tipoAlerta}</span>
      </td>
      <td className={`${tdCls} text-muted-foreground`}>{numeroIncidente ?? "—"}</td>
      <td className={tdCls}>
        <div className="max-w-[420px]">{alerta.descripcion ?? "—"}</div>
        {alerta.justificacion && (
          <div className="mt-0.5 text-xs text-muted-foreground">
            Motivo: {alerta.justificacion}
          </div>
        )}
      </td>
      <td className={`${tdCls} text-right tabular-nums ${riesgoClass(alerta.riesgo)}`}>
        {Math.round(alerta.riesgo * 100)}%
      </td>
      <td className={tdCls}>
        <Badge variant={estilo.variant}>{estilo.label}</Badge>
      </td>
      <td className={`${tdCls} text-right whitespace-nowrap`}>
        {(TRANSICIONES_ALERTA[alerta.estado] ?? []).map((t) => (
          <button
            key={t.estado}
            disabled={updating}
            onClick={() => {
              // Para ALT009 tanto "Revisar" como "Resolver" llevan al mismo lugar: no
              // hay nada que revisar sin antes cargar la sucursal faltante en Tabla KM.
              const abreCargaSucursal =
                alerta.tipoAlerta === CODIGO_ALT009 &&
                !t.pideJustificacion &&
                (alerta.estado === "pendiente" || alerta.estado === "en_revision");
              if (abreCargaSucursal) onResolverAlt009(alerta);
              else if (t.pideJustificacion) onDescartar(alerta);
              else void cambiar(t.estado);
            }}
            className="ml-3 font-body text-xs text-brand-orange hover:underline disabled:opacity-50"
          >
            {t.label}
          </button>
        ))}
      </td>
    </tr>
  );
}
