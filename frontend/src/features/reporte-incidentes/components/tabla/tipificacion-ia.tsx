"use client";

import { useState, type ReactNode } from "react";
import { AlertTriangle, CheckCircle2, Info, Loader2, RotateCw, X } from "lucide-react";
import type { EstadoDashboard } from "../../hooks/use-reporte";
import { useTipificacionIA } from "../../hooks/use-tipificacion-ia";
import { Button } from "@/shared/components/ui/button";
import { cn } from "@/shared/utils/cn";
import { CLASE_BOTON_NARANJA } from "./estilos";

/** Segundos con un decimal, como el cronómetro del legacy ("12,3 s"). */
function segundos(ms: number): string {
  return `${(ms / 1000).toLocaleString("es-AR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} s`;
}

function casos(n: number): string {
  return `${n.toLocaleString("es-AR")} caso${n === 1 ? "" : "s"}`;
}

/** Toast flotante abajo a la derecha, con el look de las cards de HDM. */
function Toast({
  icono,
  tonoIcono,
  titulo,
  derecha,
  children,
  onCerrar,
}: {
  icono: ReactNode;
  tonoIcono: string;
  titulo: string;
  derecha?: ReactNode;
  children?: ReactNode;
  onCerrar?: () => void;
}) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed right-4 bottom-4 z-[90] flex w-[calc(100vw-32px)] max-w-[360px] items-start gap-3.5 rounded-[12px] border border-border bg-card p-3.5 font-body shadow-[0_12px_32px_rgba(0,0,0,0.45)] sm:right-8 sm:bottom-8"
    >
      <span className={cn("flex h-9 w-9 flex-none items-center justify-center rounded-[10px]", tonoIcono)}>{icono}</span>
      <div className="flex min-w-0 grow flex-col gap-1">
        <div className="flex items-baseline justify-between gap-3">
          <span className="text-sm font-bold text-foreground">{titulo}</span>
          {derecha}
        </div>
        {children && <div className="text-xs text-muted-foreground">{children}</div>}
      </div>
      {onCerrar && (
        <button
          type="button"
          aria-label="Cerrar aviso"
          onClick={onCerrar}
          className="-mt-1 -mr-1 flex cursor-pointer rounded-[6px] p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      )}
    </div>
  );
}

/** Aviso para quien no puede tipificar: no dispara nada, solo informa. */
function AvisoSinPermiso({ pendientes }: { pendientes: number }) {
  const [cerrado, setCerrado] = useState(false);
  if (cerrado) return null;
  return (
    <Toast
      icono={<Info className="h-[18px] w-[18px]" aria-hidden="true" />}
      tonoIcono="bg-muted text-muted-foreground"
      titulo="Casos sin tipificar"
      onCerrar={() => setCerrado(true)}
    >
      {casos(pendientes)} del período esperan la tipificación con IA, que la dispara alguien con permiso de edición.
    </Toast>
  );
}

/** Port de `ClassificationRefiner`: tipifica con IA en segundo plano los casos
 * que llegaron sin tipificar y avisa el avance con un toast. */
export function TipificacionIA({ estado }: { estado: EstadoDashboard }) {
  const ia = useTipificacionIA(estado);
  const naranja = "bg-brand-orange/10 text-brand-orange";

  if (!estado.canUpdate) {
    return ia.pendientes > 0 ? <AvisoSinPermiso key={estado.version} pendientes={ia.pendientes} /> : null;
  }

  switch (ia.fase) {
    case "tipificando":
      return (
        <Toast
          icono={<Loader2 className="h-[18px] w-[18px] animate-spin" aria-hidden="true" />}
          tonoIcono={naranja}
          titulo="Tipificando con IA…"
          derecha={<span className="font-heading text-sm font-bold tabular-nums text-brand-orange">{segundos(ia.transcurridoMs)}</span>}
        >
          {casos(ia.pendientes)} sin tipificar en el período. El reporte se actualiza solo al terminar.
        </Toast>
      );
    case "exito":
      return (
        <Toast
          icono={<CheckCircle2 className="h-[18px] w-[18px]" aria-hidden="true" />}
          tonoIcono="bg-success/10 text-success"
          titulo="Tipificación completada"
          onCerrar={ia.cerrar}
        >
          {casos(ia.resultado?.tipificados ?? 0)} en {segundos(ia.transcurridoMs)}
          {(ia.resultado?.fallidos ?? 0) > 0 && ` · ${casos(ia.resultado?.fallidos ?? 0)} sin respuesta de la IA`}
        </Toast>
      );
    case "saturada":
    case "error":
      return (
        <Toast
          icono={<AlertTriangle className="h-[18px] w-[18px]" aria-hidden="true" />}
          tonoIcono="bg-warning/10 text-warning"
          titulo={ia.fase === "saturada" ? "IA saturada" : "No se pudo tipificar"}
          onCerrar={ia.cerrar}
        >
          <p>
            {ia.fase === "saturada"
              ? `No se tipificó ningún caso (${segundos(ia.transcurridoMs)}). Los ${casos(ia.pendientes)} siguen pendientes.`
              : ia.mensaje}
          </p>
          <Button size="sm" className={cn(CLASE_BOTON_NARANJA, "mt-2 h-7 px-2.5")} onClick={ia.reintentar}>
            <RotateCw className="h-3.5 w-3.5" aria-hidden="true" />
            Reintentar
          </Button>
        </Toast>
      );
    case "no_configurada":
      return (
        <Toast
          icono={<Info className="h-[18px] w-[18px]" aria-hidden="true" />}
          tonoIcono={naranja}
          titulo="Tipificación con IA no disponible"
          onCerrar={ia.cerrar}
        >
          {ia.mensaje}
        </Toast>
      );
    default:
      return null;
  }
}
