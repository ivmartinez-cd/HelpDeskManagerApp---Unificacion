"use client";

import { ChevronDown, ChevronRight, ExternalLink, History, Route } from "lucide-react";
import Link from "next/link";
import { cn } from "@/shared/utils/cn";
import { incidentUrl } from "@/shared/utils/incident-link";
import { useSeleccionAlertas } from "../hooks/seleccion-alertas-context";
import type { Alerta, Incidente, PrestadorLiquidacion } from "../types/liquidaciones";
import { peorTonoActivo } from "../lib/alerta-estados";
import { formatARS, formatFechaDia } from "../lib/format";
import { AlertaSubRow } from "./alerta-sub-row";
import { EstadoValidacionBadge, TipoBadge } from "./incidente-badges";

const CODIGO_ALT010 = "ALT010";
const CODIGO_ALT005 = "ALT005";

/** La alerta individual de ALT005 (`es_grupo=false`) es el mismo hallazgo que
 * la de grupo cuando ambas caen en el mismo incidente — se oculta acá para no
 * hacer gestionar dos veces lo mismo. El backend cascadea el estado de la de
 * grupo a la individual oculta (`actualizar_estado_alerta.py`), así que no
 * queda huérfana. */
function alertasSinDuplicadoAlt005(alertas: Alerta[]): Alerta[] {
  const hayGrupo = alertas.some((a) => a.tipoAlerta === CODIGO_ALT005 && a.esGrupo);
  if (!hayGrupo) return alertas;
  return alertas.filter((a) => !(a.tipoAlerta === CODIGO_ALT005 && !a.esGrupo));
}

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
  const alertasVisibles = alertasSinDuplicadoAlt005(alertasInc);
  // Severidad de la fila SIN expandir: la peor entre las alertas activas
  // (pendiente/en_revisión) — así la TL distingue qué incidente necesita
  // atención sin tener que abrir cada uno con la flecha (pedido de Iván,
  // 2026-09-08). Si todas las alertas ya están resueltas/descartadas, no
  // hay tono (mismo criterio que `estado_validacion === "ok"` en backend).
  const tono = hasAlertas ? peorTonoActivo(alertasInc) : null;
  const Icon = tono?.icon;
  // Tuvo alerta pero ya no queda ninguna activa: marca distinta a "nunca tuvo
  // nada" para que la TL vea que hubo un caso y se cerró (pedido de Iván,
  // 2026-09-09 — antes ambos casos se veían idénticos sin abrir la fila).
  const huboAlertaCerrada = hasAlertas && !tono;
  return (
    <>
      <tr
        id={`incidente-row-${incidente.id}`}
        className={cn(
          "border-t border-border transition-colors hover:bg-muted/30",
          hasAlertas ? "cursor-pointer" : "cursor-default",
          tono && cn("border-l-[4px]", tono.rowBorder, tono.rowBg),
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
            {Icon ? (
              <Icon size={13} strokeWidth={2.4} className={cn("flex-shrink-0", tono?.pillText)} aria-hidden="true" />
            ) : (
              huboAlertaCerrada && (
                <span
                  title={`Tuvo ${alertasInc.length} alerta${alertasInc.length > 1 ? "s" : ""}, ya cerrada${alertasInc.length > 1 ? "s" : ""}`}
                >
                  <History size={13} strokeWidth={2.4} className="flex-shrink-0 text-muted-foreground" aria-hidden="true" />
                </span>
              )
            )}
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
          ) : incidente.empresaNombre && incidente.sucursalNombre ? (
            <Link
              href={`/liquidaciones/configuracion/tabla-km?${new URLSearchParams({
                prestadorId,
                empresa: incidente.empresaNombre,
                sucursal: incidente.sucursalNombre,
              })}`}
              onClick={(e) => e.stopPropagation()}
              title="Falta esta empresa/sucursal en Tabla KM — cargarla acá"
              className="text-xs font-semibold text-warning underline decoration-dotted hover:opacity-80"
            >
              Sin tabla
            </Link>
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
          <EstadoValidacionBadge estado={incidente.estadoValidacion} tonoTexto={tono?.pillText} />
        </td>
      </tr>
      {expanded &&
        alertasVisibles.map((a) => (
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
