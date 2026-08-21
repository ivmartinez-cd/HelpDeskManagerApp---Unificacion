"use client";

import { Badge } from "@/shared/components/ui/badge";
import { cn } from "@/shared/utils/cn";
import type { Alerta } from "../types/liquidaciones";
import { ESTADO_ALERTA_STYLES } from "../lib/alerta-estados";
import { riesgoClass } from "./incidente-badges";

/** Fila expandida de una alerta de un incidente, extraída de
 * `incidentes-tabla.tsx` porque ese archivo ya superaba el tamaño máximo de
 * archivo (§4). */
export function AlertaSubRow({ alerta }: { alerta: Alerta }) {
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
