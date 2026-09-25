"use client";

import { useState, type ReactNode } from "react";
import { ExternalLink, Tag } from "lucide-react";
import { PENDIENTE, type Incidente } from "../../types/reporte";
import type { EstadoDashboard } from "../../hooks/use-reporte";
import { cn } from "@/shared/utils/cn";
import { Button } from "@/shared/components/ui/button";
import { BitacoraIncidente } from "./bitacora-incidente";
import { EditorTipificacion } from "./editor-tipificacion";
import { CLASE_BOTON, CLASE_ETIQUETA, URL_WEBAGENTES } from "./estilos";

/** Color del estado del caso (mismo criterio que `getEstadoStyle` del legacy). */
export function claseEstadoCaso(estado: string | null): string {
  const e = (estado ?? "").toLowerCase();
  if (e === "resuelto" || e === "cerrado") return "text-success bg-success/10";
  if (e === "abierto") return "text-info bg-info/10";
  return "text-warning bg-warning/10";
}

const PALABRAS_NOTA_INTERNA = ["sicop", "llamar a la ma", "153017"];

/** "Motivo — item · item · item": el motivo va destacado y los items en
 * lista; las notas internas se marcan y "funcionamiento ok" se descarta. */
function ReporteCliente({ texto }: { texto: string }) {
  if (!texto) return <>—</>;
  const [motivo, ...resto] = texto.split(/\s*—\s*/);
  const items = resto
    .join(" — ")
    .split(/\s*·\s*/)
    .map((i) => i.trim())
    .filter((i) => i && !i.toLowerCase().includes("funcionamiento ok"));
  return (
    <div className="flex flex-col gap-2">
      <p className="font-semibold">{motivo}</p>
      {items.length > 0 && (
        <ul className="list-disc space-y-1 pl-5">
          {items.map((item, i) => {
            const interna = PALABRAS_NOTA_INTERNA.some((p) => item.toLowerCase().includes(p));
            return (
              <li key={i} className={cn("text-[13px]", interna ? "italic text-muted-foreground" : "text-foreground")}>
                {item}
                {interna && (
                  <span className="ml-1.5 rounded-[4px] border border-warning/40 bg-warning/10 px-1 font-body text-[10px] font-semibold not-italic text-warning">
                    Nota interna
                  </span>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

function Dato({ etiqueta, children, pie }: { etiqueta: string; children: ReactNode; pie?: ReactNode }) {
  return (
    <div className="flex min-w-0 flex-col gap-1">
      <span className={CLASE_ETIQUETA}>{etiqueta}</span>
      <div className="font-body text-sm text-foreground">{children}</div>
      {pie && <div className="font-body text-xs text-muted-foreground">{pie}</div>}
    </div>
  );
}

function Recuadro({ etiqueta, children }: { etiqueta: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className={CLASE_ETIQUETA}>{etiqueta}</span>
      <div className="rounded-[10px] border border-border bg-card px-3.5 py-3 font-body text-sm leading-relaxed text-foreground">
        {children}
      </div>
    </div>
  );
}

export function PildoraTipificacion({ incidente, color }: { incidente: Incidente; color?: string }) {
  const categoria = incidente.categoria ?? PENDIENTE;
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 font-body text-[13px] text-foreground">
      <span className="h-2 w-2 flex-none rounded-[2px]" style={{ background: color ?? "var(--muted-foreground)" }} />
      {categoria}
      {incidente.subcategoria && (
        <>
          <span className="text-muted-foreground">›</span>
          <strong className="font-semibold">{incidente.subcategoria}</strong>
        </>
      )}
    </span>
  );
}

function CorreccionTipificacion({ incidente, estado }: { incidente: Incidente; estado: EstadoDashboard }) {
  const [abierto, setAbierto] = useState(false);
  if (!abierto) {
    return (
      <Button variant="outline" size="sm" className={cn(CLASE_BOTON, "self-start")} onClick={() => setAbierto(true)}>
        <Tag className="h-3.5 w-3.5 text-brand-orange" aria-hidden="true" />
        Corregir tipificación
      </Button>
    );
  }
  return (
    <div className="flex flex-col gap-3 rounded-[12px] border border-border bg-card px-5 py-4">
      <div className="flex items-center gap-2">
        <Tag className="h-4 w-4 text-brand-orange" aria-hidden="true" />
        <h3 className="font-heading text-sm font-bold text-foreground">Nueva tipificación</h3>
      </div>
      <EditorTipificacion
        incidente={incidente}
        taxonomia={estado.reporte?.taxonomia ?? []}
        onGuardado={() => {
          setAbierto(false);
          estado.recargar();
        }}
        onCancelar={() => setAbierto(false)}
      />
      <p className="font-body text-xs text-muted-foreground">
        Se aplica a todos los casos con el mismo reporte, causa y solución, y se recalculan los reportes de este cliente.
      </p>
    </div>
  );
}

/** Detalle expandido de un incidente (port de `IncidentDetails`). */
export function DetalleIncidente({ incidente, estado }: { incidente: Incidente; estado: EstadoDashboard }) {
  const color = incidente.categoria ? estado.reporte?.colores[incidente.categoria] : undefined;
  return (
    <div className="flex flex-col gap-5 pt-1">
      <div className="flex flex-wrap items-center gap-3">
        <span
          className={cn(
            "rounded-full px-2 py-0.5 font-body text-[10px] font-bold uppercase tracking-[.025em]",
            claseEstadoCaso(incidente.estado),
          )}
        >
          {incidente.estado ?? "—"}
        </span>
        <PildoraTipificacion incidente={incidente} color={color} />
        <a
          href={`${URL_WEBAGENTES}${incidente.numero}`}
          target="_blank"
          rel="noopener noreferrer"
          className="ml-auto inline-flex items-center gap-1.5 font-body text-[13px] font-semibold text-brand-orange hover:underline"
        >
          Ver en webagentes
          <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
        </a>
      </div>

      <div className="grid grid-cols-1 gap-x-8 gap-y-5 rounded-[12px] border border-border bg-card p-5 sm:grid-cols-2 lg:grid-cols-3">
        <Dato etiqueta="Solicitante">{incidente.solicitante ?? "No especificado"}</Dato>
        <Dato etiqueta="Técnico asignado">{incidente.tecnico ?? "No asignado"}</Dato>
        <Dato etiqueta="Tipo de trabajo">{incidente.tipo_trabajo ?? "Correctivo"}</Dato>
        <Dato etiqueta="Equipo">{incidente.articulo ?? "Impresora"}</Dato>
        <Dato etiqueta="Serie">{incidente.maquina ?? "—"}</Dato>
        <Dato etiqueta="Fechas del caso" pie={incidente.fecha_cierre ? `Cierre: ${incidente.fecha_cierre}` : undefined}>
          Apertura: {incidente.fecha}
        </Dato>
      </div>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <Recuadro etiqueta="Reporte del cliente">
          <ReporteCliente texto={incidente.descripcion} />
        </Recuadro>
        {incidente.causa && <Recuadro etiqueta="Causa diagnosticada">{incidente.causa}</Recuadro>}
      </div>

      <BitacoraIncidente trabajos={incidente.trabajos} solucion={incidente.solucion} />

      {estado.canUpdate && <CorreccionTipificacion incidente={incidente} estado={estado} />}
    </div>
  );
}
