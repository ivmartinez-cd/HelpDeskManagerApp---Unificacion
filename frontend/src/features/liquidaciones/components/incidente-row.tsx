"use client";

import { ChevronDown, ChevronRight, ExternalLink, Route } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { incidentUrl } from "@/shared/utils/incident-link";
import { useSeleccionAlertas } from "../hooks/seleccion-alertas-context";
import type { Alerta, Incidente, PrestadorLiquidacion } from "../types/liquidaciones";
import { formatARS, formatFechaDia } from "../lib/format";
import { AlertaSubRow } from "./alerta-sub-row";
import { EstadoValidacionBadge, TipoBadge } from "./incidente-badges";

const CODIGO_ALT010 = "ALT010";

/** Fila de un incidente (+ sus alertas expandidas), extraída de
 * `incidentes-tabla.tsx` porque ese archivo ya superaba el tamaño máximo de
 * archivo (§4). */
export function IncidenteRow({
  liquidacionId,
  prestadorId,
  prestadores,
  incidente,
  incidentesById,
  alertasInc,
  expanded,
  isRutaCompartida,
  onToggle,
  onAlertaChanged,
}: {
  liquidacionId: string;
  prestadorId: string;
  prestadores: PrestadorLiquidacion[];
  incidente: Incidente;
  incidentesById: Record<string, Incidente>;
  alertasInc: Alerta[];
  expanded: boolean;
  isRutaCompartida: boolean;
  onToggle: () => void;
  onAlertaChanged: () => void;
}) {
  const tdCls = "py-3 px-4 font-body text-sm text-foreground";
  // Tilde de selección múltiple (gestión de alertas en lote): solo incidentes
  // con alertas abiertas; el resto deja el hueco para alinear la columna.
  const seleccion = useSeleccionAlertas();
  const seleccionable = seleccion?.esSeleccionable(incidente.id) ?? false;
  const serieDuplicada = alertasInc.find((a) => a.tipoAlerta === CODIGO_ALT010);
  const diff =
    incidente.costoServicioEsperado !== null
      ? incidente.costoServicioCobrado - incidente.costoServicioEsperado
      : null;
  const hasAlertas = alertasInc.length > 0;
  return (
    <>
      <tr
        id={`incidente-row-${incidente.id}`}
        className={cn(
          "border-t border-border transition-colors hover:bg-muted/30",
          hasAlertas ? "cursor-pointer" : "cursor-default",
        )}
        onClick={hasAlertas ? onToggle : undefined}
      >
        <td className={tdCls}>
          <div className="flex items-center gap-1.5">
            {seleccion &&
              (seleccionable ? (
                <input
                  type="checkbox"
                  aria-label={`Seleccionar incidente ${incidente.numeroIncidente}`}
                  checked={seleccion.seleccionados.has(incidente.id)}
                  onChange={() => seleccion.toggle(incidente.id)}
                  onClick={(e) => e.stopPropagation()}
                  className="h-3.5 w-3.5 flex-shrink-0 accent-brand-orange"
                />
              ) : (
                <span className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
              ))}
            {hasAlertas &&
              (expanded ? (
                <ChevronDown size={12} className="flex-shrink-0 text-muted-foreground" />
              ) : (
                <ChevronRight size={12} className="flex-shrink-0 text-muted-foreground" />
              ))}
            <a
              href={incidentUrl(incidente.numeroIncidente)}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-brand-orange hover:underline"
            >
              {incidente.numeroIncidente}
            </a>
          </div>
        </td>
        <td className={tdCls}>
          {incidente.nroSerie ? (
            <span className={cn(serieDuplicada && "font-semibold text-warning")}>
              {incidente.nroSerie}
              {serieDuplicada && (
                <span
                  className="ml-1"
                  title={serieDuplicada.descripcion ?? "Serie duplicada (ALT010)"}
                >
                  ⚠
                </span>
              )}
            </span>
          ) : (
            <span className="text-muted-foreground">—</span>
          )}
        </td>
        <td className={tdCls}>
          <div className="flex items-center gap-1.5">
            <span>
              {[incidente.empresaNombre, incidente.sucursalNombre].filter(Boolean).join(" / ") ||
                "—"}
            </span>
            {isRutaCompartida && (
              <span title="Posible ruta compartida: otro incidente del mismo día comparte destino o localidad">
                <Route size={12} className="flex-shrink-0 text-brand-orange" />
              </span>
            )}
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
            <div className="mt-0.5 font-body text-xs text-muted-foreground">
              {incidente.localidadCliente}
            </div>
          )}
        </td>
        <td className={tdCls}>
          <TipoBadge tipo={incidente.tipo} />
        </td>
        <td className={`${tdCls} text-right`}>
          {Math.round(incidente.cantKmCobrado).toLocaleString("es-AR")}
        </td>
        <td className={`${tdCls} text-right`}>
          {incidente.cantKmEsperado !== null ? (
            <span className="font-semibold text-success">
              {Math.round(incidente.cantKmEsperado).toLocaleString("es-AR")}
            </span>
          ) : (
            <span className="text-xs font-semibold text-warning">Sin tabla</span>
          )}
        </td>
        <td className={`${tdCls} text-right`}>{formatARS(incidente.costoServicioCobrado)}</td>
        <td className={`${tdCls} text-right text-muted-foreground`}>
          {incidente.costoServicioEsperado !== null
            ? formatARS(incidente.costoServicioEsperado)
            : "—"}
        </td>
        <td
          className={cn(
            `${tdCls} text-right`,
            diff !== null && (diff > 0 ? "text-destructive" : "text-success"),
          )}
        >
          {diff !== null ? formatARS(diff) : "—"}
        </td>
        <td className={`${tdCls} text-muted-foreground`}>
          {incidente.fechaCierre ? formatFechaDia(incidente.fechaCierre) : "—"}
        </td>
        <td className={tdCls}>
          <EstadoValidacionBadge estado={incidente.estadoValidacion} />
        </td>
      </tr>
      {expanded &&
        alertasInc.map((a) => (
          <AlertaSubRow
            key={a.id}
            liquidacionId={liquidacionId}
            prestadorId={prestadorId}
            prestadores={prestadores}
            incidentesById={incidentesById}
            alerta={a}
            onChanged={onAlertaChanged}
          />
        ))}
    </>
  );
}
