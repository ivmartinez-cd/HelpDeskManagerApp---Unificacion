"use client";

import { useState } from "react";
import { Route } from "lucide-react";
import { Badge } from "@/shared/components/ui/badge";
import { cn } from "@/shared/utils/cn";
import type { Alerta, Incidente, PrestadorLiquidacion } from "../types/liquidaciones";
import { ESTADO_ALERTA_STYLES } from "../lib/alerta-estados";
import { GestionarAlertaModal } from "./gestionar-alerta-modal";
import { riesgoClass } from "./incidente-badges";

/** Resalta brevemente la fila del incidente vinculado y hace scroll hasta
 * ella — puede estar en la sección Correctivos o Preventivos, ambas montadas
 * a la vez en la misma página (ver `incidente-row.tsx`, `id={incidente-row-*}`). */
function saltarAIncidente(incidenteId: string) {
  const el = document.getElementById(`incidente-row-${incidenteId}`);
  if (!el) return;
  el.scrollIntoView({ behavior: "smooth", block: "center" });
  el.classList.add("bg-brand-orange/10");
  setTimeout(() => el.classList.remove("bg-brand-orange/10"), 1500);
}

/** Fila expandida de una alerta de un incidente, extraída de
 * `incidentes-tabla.tsx` porque ese archivo ya superaba el tamaño máximo de
 * archivo (§4). "Gestionar" abre un modal para resolver/descartar la
 * alerta ahí mismo, en vez de saltar a la sección "Alertas" (removida). */
export function AlertaSubRow({
  liquidacionId,
  prestadorId,
  prestadores,
  incidentesById,
  alerta,
  onChanged,
}: {
  liquidacionId: string;
  prestadorId: string;
  prestadores: PrestadorLiquidacion[];
  incidentesById: Record<string, Incidente>;
  alerta: Alerta;
  onChanged: () => void;
}) {
  const [gestionando, setGestionando] = useState(false);
  const tdCls = "py-2 px-4 font-body text-xs";
  const estilo = ESTADO_ALERTA_STYLES[alerta.estado] ?? ESTADO_ALERTA_STYLES.pendiente;
  const relacionado = alerta.incidenteRelacionadoId
    ? incidentesById[alerta.incidenteRelacionadoId]
    : undefined;
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
        {relacionado && (
          <button
            type="button"
            onClick={() => saltarAIncidente(relacionado.id)}
            title="Ir al incidente donde se cobraron estos km"
            className="ml-2 inline-flex items-center gap-1 font-semibold text-brand-orange hover:underline"
          >
            <Route size={12} /> Ruta con #{relacionado.numeroIncidente}
          </button>
        )}
      </td>
      <td className={cn(tdCls, "text-right", riesgoClass(alerta.riesgo))}>
        {Math.round(alerta.riesgo * 100)}%
      </td>
      <td className={tdCls} colSpan={6}>
        <span className="flex items-center gap-3">
          <Badge variant={estilo.variant}>{estilo.label}</Badge>
          <button
            type="button"
            onClick={() => setGestionando(true)}
            className="font-semibold text-brand-orange hover:underline"
          >
            Gestionar
          </button>
        </span>
      </td>
      {gestionando && (
        <GestionarAlertaModal
          liquidacionId={liquidacionId}
          prestadorId={prestadorId}
          prestadores={prestadores}
          incidentesById={incidentesById}
          alerta={alerta}
          onClose={() => setGestionando(false)}
          onChanged={onChanged}
        />
      )}
    </tr>
  );
}
