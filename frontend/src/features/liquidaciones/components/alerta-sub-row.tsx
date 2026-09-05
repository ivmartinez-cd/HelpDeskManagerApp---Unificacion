"use client";

import { useState } from "react";
import { Route } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/shared/components/ui/badge";
import { cn } from "@/shared/utils/cn";
import type { Alerta, Incidente, PrestadorLiquidacion } from "../types/liquidaciones";
import { ESTADO_ALERTA_STYLES } from "../lib/alerta-estados";
import { formatARS } from "../lib/format";
import { GestionarAlertaModal } from "./gestionar-alerta-modal";
import { riesgoClass } from "./incidente-badges";

const CODIGO_ALT008 = "ALT008";

/** ALT008 = "Sin tarifario". `datosContexto` es un passthrough del dict Python
 * del motor de reglas (`alt008_tarifario.py`) — sus claves quedan tal cual se
 * armaron ahí (snake_case), no se re-mapean a camelCase como el resto del DTO.
 *
 * `spst_id` en null NO significa "falta la tarifa": significa que la fila de
 * Tabla KM de este incidente todavía no tiene SPST vinculado, así que el
 * motor nunca llegó a buscar una tarifa — el arreglo real es vincular el
 * SPST (la tarifa puede ya existir para ese SPST). Solo cuando el SPST SÍ se
 * resolvió y aun así no hay tarifario, el faltante real es la tarifa. */
function linkFaltante(
  prestadorId: string,
  alerta: Alerta,
  incidentesById: Record<string, Incidente>,
): { href: string; label: string; title: string } | null {
  if (alerta.tipoAlerta !== CODIGO_ALT008) return null;
  const ctx = alerta.datosContexto as { tipo_servicio?: string; spst_id?: string | null } | null;
  if (!ctx?.tipo_servicio) return null;

  if (ctx.spst_id) {
    const params = new URLSearchParams({ prestadorId, tipoServicio: ctx.tipo_servicio, spstId: ctx.spst_id });
    return {
      href: `/liquidaciones/configuracion/tarifarios?${params}`,
      label: "Cargar tarifa →",
      title: "El SPST ya está resuelto y no tiene tarifa cargada — completarla en Tarifarios",
    };
  }

  const incidente = incidentesById[alerta.incidenteId];
  const query = incidente?.sucursalNombre || incidente?.empresaNombre;
  if (!query) return null;
  const params = new URLSearchParams({ prestadorId, buscar: query });
  return {
    href: `/liquidaciones/configuracion/tabla-km?${params}`,
    label: "Vincular SPST →",
    title: "Sin SPST vinculado en Tabla KM — por eso no se puede resolver la tarifa",
  };
}

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
  const faltante = linkFaltante(prestadorId, alerta, incidentesById);
  return (
    <tr className="border-l-[3px] border-l-destructive/30 bg-destructive/[0.04]">
      <td className={cn(tdCls, "pl-7")} colSpan={4}>
        <span className="font-semibold text-foreground">{alerta.tipoAlerta}</span>
        {alerta.esGrupo && (
          <span
            className="ml-2 rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-bold uppercase text-muted-foreground"
            title={`Agrupa ${alerta.grupoIncidenteIds.length} incidentes del mismo corredor`}
          >
            Grupo ({alerta.grupoIncidenteIds.length})
          </span>
        )}
        {alerta.descripcion && (
          <span className="ml-2 text-muted-foreground">{alerta.descripcion}</span>
        )}
        {alerta.esGrupo && alerta.diferencia !== null && (
          <span className="ml-2 text-muted-foreground">
            Cobrado {formatARS(alerta.montoCobrado ?? 0)} vs. esperado{" "}
            {formatARS(alerta.montoEsperado ?? 0)}
          </span>
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
        {Math.round(alerta.riesgo)}%
      </td>
      <td className={tdCls} colSpan={6}>
        <span className="flex items-center gap-3">
          <Badge variant={estilo.variant}>{estilo.label}</Badge>
          {faltante && (
            <Link
              href={faltante.href}
              title={faltante.title}
              className="font-semibold text-brand-orange hover:underline"
            >
              {faltante.label}
            </Link>
          )}
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
